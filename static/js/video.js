import { logger } from './logger';

let apiClient;

// add initialization hook
add_init_function(init);

const localVideo = document.querySelector('#localVideo');
const remoteVideo = document.querySelector('#remoteVideo');

let isChannelReady = false;
let isInitiator = false;
let isStarted = false;

let localStream;
let pc;
let remoteStream;
let turnReady;

let onlineClients;

let remoteClient = null;
const localClient = { username: username, client_id: clientId };

// const turnServer = 'https://computeengineondemand.appspot.com/turn?username=41784574&key=4080218913';
const turnServer = null;

// initialization function
function init (client) {

    logger.log('info', '> video.js');

    // set apiClient
    apiClient = client;

    // retrieve online clients
    retrieveOnlineClients();

    // signup for client webrtc updates
    logger.log('info', 'Signing up for client webrtc updates');
    apiClient.subscribeToWebRTC((message) => handleMessages(parseMessage(message)) );

}

// Ready function
let callButton;
let hangupButton;
$(function () {

    callButton = $('#callButton');
    hangupButton = $('#hangupButton');

    // disable buttons
    callButton.prop('disabled', true);
    hangupButton.prop('disabled', true);

    // call button click
    callButton
        .click(function() {
            if (state === State.IDLE && remoteClient !== null) {
                if (typeof localStream !== 'undefined') {
                    startStream();
                }
                state = State.CALLING;
                callButton.prop('disabled', true);
                hangupButton.prop('disabled', false);
                sendMessage(remoteClient, {type: 'call'});
            }
        });

    // hangup button click
    hangupButton
        .click(function() {
            if (state === State.ACTIVE_CALL) {
                // reset dropdown
                $("#clients-dropdown").val('default').selectpicker("refresh");
                callButton.prop('disabled', true);
                hangupButton.prop('disabled', true);
                hangup();
            }
        });

});

// online clients

function retrieveOnlineClients() {
    apiClient.getClients()
        .then( (clients) => {
            logger.log('info', '%d clients retrieved', Object.keys(clients).length);
            onlineClients = clients;
            const dropdown = $('#clients-dropdown');
            dropdown.empty();
            for (const remote of onlineClients) {
                if (remote.client_id !== clientId) {
                    const html = `<a class="dropdown-item" href="#" id="${remote.username}_${remote.client_id}">${remote.username} @ ${remote.client_id}</a>`;
                    dropdown.append(html);
                    $(`#${remote.username}_${remote.client_id}`).click(function() {
                        if (state === State.IDLE) {
                            remoteClient = {...remote};
                            callButton.prop('disabled', false);
                            hangupButton.prop('disabled', true);
                        } else {
                            logger.log('error', 'Cannot select client when not IDLE');
                        }
                    });

                }
            }
        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve clients from ApiClient: %j', error);
        })
}

// State machine and message handling

const State = {
    IDLE: 1,
    CALLING: 2,
    WAITING_FOR_ANSWER: 3,
    WAITING_FOR_OFFER: 4,
    ACTIVE_CALL: 5,
};
Object.freeze(State);
let state = State.IDLE;

// handle messages
function handleMessages(message) {

    if (message.type === 'call') {

        logger.log('info', 'GOT CALL');

        if (state !== State.IDLE) {
            // reply busy, does not change state
            logger.log('info', 'BUSY: rejecting call from %j', message.client);
            sendMessage(message.client, { type: 'busy' });
        } else {
            // accept call
            state = State.WAITING_FOR_OFFER;
            logger.log('info', 'ACCEPTED: accepting call from %j', message.client);
            remoteClient = {...message.client};
            sendMessage(message.client, { type: 'accepted' });
        }

    } else if (message.type === 'busy') {

        logger.log('info', 'GOT BUSY');

        if (state === State.CALLING &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {
            // cancel call, remote is busy, go back to idle
            state = State.IDLE;
            remoteClient = null;
            logger.log('info', 'CANCELLING CALL: remote is busy: %j', message.client);
        } else {
            // ignore
            logger.log('info', 'IGNORING BUSY: %j', message.client);
        }

    } else if (message.type === 'accepted') {

        logger.log('info', 'GOT ACCEPTED');

        if (state === State.CALLING &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            // Make offer
            state = State.WAITING_FOR_ANSWER;
            logger.log('info', 'ACCEPTED: will make offer to %j', message.client);
            isInitiator = true;
            maybeStart();

        } else {

            // ignore
            logger.log('info', 'IGNORING ACCEPTED: %j', message.client);

        }

    } else if (message.type === 'offer') {

        logger.log('info', 'GOT OFFER');

        if (state === State.WAITING_FOR_OFFER &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            logger.log('info', 'will answer to %j', message.client);
            state = State.ACTIVE_CALL;
            if (!isInitiator && !isStarted) {
                maybeStart();
            }
            pc.setRemoteDescription(new RTCSessionDescription(message));
            doAnswer();

        } else {

            // ignore
            logger.log('info', 'IGNORING OFFER: %j', message.client);

        }

    } else if (message.type === 'answer') {

        logger.log('info', 'GOT ANSWER');

        if (state === State.WAITING_FOR_ANSWER &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            pc.setRemoteDescription(new RTCSessionDescription(message));

        } else {

            // ignore
            logger.log('info', 'IGNORING ANSWER: %j', message.client);

        }

    } else if (message.type === 'candidate') {

        logger.log('info', 'GOT CANDIDATE');

        if (state === State.ACTIVE_CALL &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            const candidate = new RTCIceCandidate({
                sdpMLineIndex: message.label,
                candidate: message.candidate
            });
            pc.addIceCandidate(candidate);

        } else {

            // ignore
            logger.log('info', 'IGNORING CANDIDATE: %j', message.client);

        }

    } else if (message.type === 'bye' && isStarted) {

        logger.log('info', 'GOT BYE');

        if (state === State.ACTIVE_CALL &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            handleRemoteHangup();

        } else {

            // ignore
            logger.log('info', 'IGNORING BYE: %j', message.client);

        }

    } else {

        // error
        logger.log('error', "Unknown message type '%s' from  %j", message.type, message.client);

    }

}

function sendMessage(peer, message) {
    if (peer === null) {
        logger.log('info', 'cannot send message %j without a peer', message);
        return;
    }

    // add client to serializer
    message = JSON.stringify(message).slice(0,-1) + "," + JSON.stringify({client: localClient}).slice(1);

    //socket.emit('message', message);
    logger.log('info', 'Client sending message: %j to %j', message, peer);
    apiClient.publish(`user/${peer.username}/client/${peer.client_id}/webrtc/message`, message, 0, false);
}

function parseMessage(message) {
    //accepting only JSON messages
    logger.log('debug', "got message: %j", message);
    let data = message.payload;
    return data;
}

// setup local stream

function gotStream(stream) {
    logger.log('info', 'Adding local stream.');
    localStream = stream;
    localVideo.srcObject = stream;
    // set channel as ready
    isChannelReady = true;
    // sendMessage('got user media');
    if (isInitiator) {
        maybeStart();
    }
}

function startStream() {

    const constraints = {
        audio: false,
        video: true
    };

    logger.log('info', "Getting user media with constraints '%j'", constraints);

    navigator.mediaDevices.getUserMedia(constraints)
        .then(gotStream)
        .catch(function(e) {
            alert('getUserMedia() error: ' + e.name);
        });

    if (location.hostname !== 'localhost' && turnServer !== null) {
        requestTurn(turnServer);
    }

}

const pcConfig = {
    'iceServers': [{
        'urls': 'stun:stun.l.google.com:19302'
    }]
};

function maybeStart() {
    logger.log('debug', '>>>>>>> maybeStart() ', isStarted, localStream, isChannelReady);
    if (!isStarted && typeof localStream !== 'undefined' && isChannelReady) {
        logger.log('info', 'creating peer connection');
        createPeerConnection();
        pc.addStream(localStream);
        isStarted = true;
        logger.log('debug', 'isInitiator = %s', isInitiator);
        if (isInitiator) {
            doOffer();
        }
    }
}

window.onbeforeunload = function() {
    sendMessage(remoteClient, {type: 'bye'});
};

/////////////////////////////////////////////////////////

function createPeerConnection() {
    try {
        pc = new RTCPeerConnection(null);
        pc.onicecandidate = handleIceCandidate;
        pc.onaddstream = handleRemoteStreamAdded;
        pc.onremovestream = handleRemoteStreamRemoved;
        logger.log('info', 'Created RTCPeerConnnection');
    } catch (e) {
        logger.log('error', 'Failed to create PeerConnection, exception: %s' + e.message);
        alert('Cannot create RTCPeerConnection object.');
    }
}

function handleIceCandidate(event) {
    logger.log('debug', 'icecandidate event: %j', event);
    if (event.candidate) {
        sendMessage(remoteClient, {
            type: 'candidate',
            label: event.candidate.sdpMLineIndex,
            id: event.candidate.sdpMid,
            candidate: event.candidate.candidate
        });
    } else {
        logger.log('debug', 'End of candidates.');
    }
}

function setLocalAndSendMessage(sessionDescription) {
    pc.setLocalDescription(sessionDescription);
    logger.log('debug', 'setLocalAndSendMessage: sending message %j', sessionDescription);
    sendMessage(remoteClient, sessionDescription);
}

function doOffer() {
    logger.log('info', 'Sending offer to peer');
    pc.createOffer()
        .then( function(offer) {
            setLocalAndSendMessage(offer);
        })
        .catch( function(reason) {
            logger.log('error', 'createOffer() error: %s', reason);
        });
}

function doAnswer() {
    logger.log('info', 'Sending answer to peer.');
    pc.createAnswer()
        .then( function(answer) {
            setLocalAndSendMessage(answer);
        })
        .catch( function(reason) {
            logger.log('error', 'createAnswer() error: %s', reason);
        });
}

function requestTurn(turnURL) {
    let turnExists = false;
    for (var i in pcConfig.iceServers) {
        if (pcConfig.iceServers[i].urls.substr(0, 5) === 'turn:') {
            turnExists = true;
            turnReady = true;
            break;
        }
    }
    if (!turnExists) {
        console.log('Getting TURN server from ', turnURL);
        // No TURN server. Get one from computeengineondemand.appspot.com:
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var turnServer = JSON.parse(xhr.responseText);
                console.log('Got TURN server: ', turnServer);
                pcConfig.iceServers.push({
                    'urls': 'turn:' + turnServer.username + '@' + turnServer.turn,
                    'credential': turnServer.password
                });
                turnReady = true;
            }
        };
        xhr.open('GET', turnURL, true);
        xhr.send();
    }
}

function handleRemoteStreamAdded(event) {
    logger.log('info', 'Remote stream added.');
    remoteStream = event.stream;
    remoteVideo.srcObject = remoteStream;
}

function handleRemoteStreamRemoved(event) {
    logger.log('info', 'Remote stream removed. Event: %j', event);
}

function hangup() {
    console.log('info', 'Hanging up.');
    stop();
    sendMessage(remoteClient, {type: 'bye'});
}

function handleRemoteHangup() {
    logger.log('info', 'Session terminated.');
    stop();
    isInitiator = false;
}

function stop() {
    isStarted = false;
    remoteClient = null;
    state = State.IDLE;
    pc.close();
    pc = null;
}
