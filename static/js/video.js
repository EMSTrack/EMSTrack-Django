import { logger } from './logger';
import {showNotification} from "./components/notification";

let apiClient;

// add initialization hook
add_init_function(initVideo);

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
const turnServerHost = null;

// initialization function
function initVideo(client) {

    logger.log('info', '> video.js');

    // set apiClient
    apiClient = client;

    // retrieve online clients
    retrieveOnlineClients();

    // signup for client webrtc updates
    logger.log('info', 'Signing up for client webrtc updates');
    apiClient.subscribeToWebRTC((message) => handleMessages(parseMessage(message)) );

    // start call?
    const hasCallDetails = (callUsername !== null && callClientId !== null);
    if (hasCallDetails) {

        const remoteClient = {
            username: callUsername,
            client_id: callClientId
        };

        if (callMode === 'new') {
            newCall(remoteClient);
        } else if (callMode === 'answer') {
            acceptCall(remoteClient);
        }

        // bring up modal
        $('#videoModalWindow').modal({
            backdrop: 'static',
            keyboard: false
        });

    }

}

// Ready function
let linkButton;
let callButton;
let remoteClientText;
$(function () {

    linkButton = $('#linkButton');
    callButton = $('#callButton');
    remoteClientText = $('#remoteClientText');

    // disable buttons
    remoteClientText.empty();
    linkButton.prop('disabled', false);
    callButton.prop('disabled', true);

    // link button click
    linkButton.click(() => { getLink(guest.username); });

    // call button click
    callButton.click(() => {
        if (state === State.ACTIVE_CALL) {
            hangup();
        } else {
            newCall();
        }
    });

    // enable video modal button
    $('#videoMenuItem').click(function() {

        // retrieve online clients
        retrieveOnlineClients();

        $('#videoModalWindow').modal({
            backdrop: 'static',
            keyboard: false,
            show: true
        });

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
                            remoteClientText.html(remoteClient.username + ' @ ' + remoteClient.client_id);

                            callButton.prop('disabled', false);
                            // hangupButton.prop('disabled', true);

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

// new link

function copyToClipboard(text) {
    window.prompt("Copy to clipboard: Ctrl+C, Enter", text);
}

function getLink(username) {

    // get token
    const uri = `${window.location.protocol}//${window.location.hostname}/guest?callUsername=${localClient.username}&callClientId=${localClient.client_id}&callMode=new`;
    logger.log('info', 'uri = %s', uri);

    apiClient.postTokenLogin(username, encodeURI(uri))
        .then( (token) => {

            logger.log('info', 'token = %j', token);
            const uri = `${window.location.protocol}//${window.location.hostname}/auth/login/${token.token}/`;
            copyToClipboard(encodeURI(uri));

        })
        .catch( (error ) => {

            logger.log('error', 'Failed to retrieve token');
            logger.log('error', error);

        });
}

// new call

function ringCall(maxTries = 5) {

    // already in a call?
    if (state !== State.CALLING)
        return;

    // should keep trying?
    if (maxTries < 0) {

        // alert call failed
        modalAlert(`${remoteClient.username}@${remoteClient.client_id} did not pick up the call`);

        // cancel call, remote did not pick up
        isStarted = false;
        state = State.IDLE;
        modalReset();

        // send cancel message
        sendMessage(remoteClient, {type: 'cancel'});

        logger.log('info', 'CANCELLING CALL: remote did not pick up call');
        return;
    }

    // add alert
    modalAlert(`Calling ${remoteClient.username}@${remoteClient.client_id}...`);

    // hangupButton.prop('disabled', false);
    sendMessage(remoteClient, {type: 'call'});

    // set timeout
    setTimeout(() => { ringCall(maxTries - 1) }, 5000);

}

function newCall(newRemoteClient = null) {

    // set remote client?
    if (newRemoteClient !== null) {
        remoteClient = {...newRemoteClient};
    }

    // initiate new call
    if (state === State.IDLE && remoteClient !== null) {
        state = State.CALLING;
        callButton.prop('disabled', true);

        ringCall();
    }
}

// accept call

function acceptCall(newRemoteClient = null) {

    // set remote client?
    let reroute = false;
    if (newRemoteClient !== null) {
        remoteClient = {...newRemoteClient};
        reroute = true;
    }

    // retrieve online clients
    retrieveOnlineClients();

    // display video modal
    $('#videoModalWindow').modal({
        backdrop: 'static',
        keyboard: false,
        show: true
    });

    // start streaming then accept call
    startStream()
        .then(function() {
            // accept call
            state = State.WAITING_FOR_OFFER;
            logger.log('info', 'ACCEPTED: accepting call from %j', remoteClient);

            remoteClientText.html(remoteClient.username + ' @ ' + remoteClient.client_id);
            // hangupButton.prop('disabled', false);

            sendMessage(remoteClient, { type: 'accepted', reroute: reroute });

            // close alert
            $('#videoAlertAlert').alert('close');
        });
}

// prompt call

function promptCall() {

    // retrieve online clients
    retrieveOnlineClients();

    // add alert
    $('#videoAlert').append(`<div class="alert alert-warning alert-dismissible fade show" id="videoAlertAlert" role="alert">
  <h4 class="alert-heading">New Video Call</h4>
  From ${remoteClient.username}@${remoteClient.client_id}
  <hr>
  <button type="button" class="btn btn-primary" id="newVideoCallAcceptButton">Accept</button>
  <button type="button" class="btn btn-secondary" data-dismiss="alert">Decline</button>
  <button type="button" class="close" data-dismiss="alert" aria-label="Close">
    <span aria-hidden="true">&times;</span>
  </button>
</div>`);

    $('#newVideoCallAcceptButton').click(() => { acceptCall(); } );

    $('#videoAlertAlert').on('closed.bs.alert', function (e) {
        if (state === State.PROMPT) {
            // decline call
            isStarted = false;
            state = State.IDLE;
            logger.log('info', 'DECLINE: declining call from %j', remoteClient);
            sendMessage(remoteClient, { type: 'decline' });
            modalReset();
        } else {
            logger.log('info', 'Unexpected state %s', state);
        }
    });

    // show notification
    showNotification('EMSTrack', 'You have a new video call request', '/static/favicon.png');

    // display video modal
    $('#videoModalWindow').modal({
        backdrop: 'static',
        keyboard: false,
        show: true
    });

}

// State machine and message handling

const State = {
    IDLE: 1,
    CALLING: 2,
    WAITING_FOR_ANSWER: 3,
    WAITING_FOR_OFFER: 4,
    ACTIVE_CALL: 5,
    PROMPT: 6,
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

            logger.log('info', 'PROMPT: will prompt user for video call from %j', message.client);

            // set state as user prompt
            state = State.PROMPT;
            remoteClient = {...message.client};

            // prompt user for new call
            promptCall();

        }

    } else if (message.type === 'busy' || message.type === 'decline') {

        logger.log('info', 'GOT BUSY OR DECLINE');

        if (state === State.CALLING &&

            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            // cancel call, remote is busy, go back to idle
            isStarted = false;
            state = State.IDLE;
            modalReset();

            // alert
            if (message.type === 'busy')
                modalAlert('Callee is busy');
            else if (message.type === 'decline')
                modalAlert('Call declined');

            logger.log('info', 'CANCELLING CALL: remote is busy or declined: %j', message.client);

        } else {

            // ignore
            logger.log('info', 'IGNORING BUSY OR DECLINE: %j', message.client);

        }

    } else if (message.type === 'accepted') {

        logger.log('info', 'GOT ACCEPTED');

        // reroute?
        if (state === State.CALLING && message.reroute) {
            remoteClient = {...message.client};
        }

        // accepted?
        if (state === State.CALLING &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            // start streaming and make offer
            startStream()
                .then(function() {

                    // Make offer
                    state = State.WAITING_FOR_ANSWER;
                    logger.log('info', 'ACCEPTED: will make offer to %j', message.client);
                    isInitiator = true;
                    maybeStart();

                    // alert
                    modalAlert('Call accepted');

                });

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

            callButton
                .removeClass('btn-success')
                .addClass('btn-danger')
                .prop('disabled', false);

        } else {

            // ignore
            logger.log('info', 'IGNORING OFFER: %j', message.client);

        }

    } else if (message.type === 'answer') {

        logger.log('info', 'GOT ANSWER');

        if (state === State.WAITING_FOR_ANSWER &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            state = State.ACTIVE_CALL;
            pc.setRemoteDescription(new RTCSessionDescription(message));

            callButton
                .removeClass('btn-success')
                .addClass('btn-danger')
                .prop('disabled', false);

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

    } else if (message.type === 'bye') {

        logger.log('info', 'GOT BYE');

        if (state === State.ACTIVE_CALL &&
            message.client.username === remoteClient.username &&
            message.client.client_id === remoteClient.client_id) {

            handleRemoteHangup();

            // alert
            modalAlert('Call terminated');

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

    if (location.hostname !== 'localhost') {
        requestTurn(turnServerHost);
    }

    // if there is nothing to do...
    if (typeof localStream !== 'undefined') {
        enableTrack(localStream, true);
        return Promise.resolve();
    }

    // otherwise start stream
    const constraints = {
        audio: true,
        video: true
    };

    logger.log('info', "Getting user media with constraints '%j'", constraints);

    return navigator.mediaDevices.getUserMedia(constraints)
        .then(gotStream)
        .catch(function(e) {
            alert('getUserMedia() error: ' + e.name);
        });

}

const pcConfig = turnServer['host'] !== '' ? {
    'iceServers': [
        {
            'url': 'stun:stun.l.google.com:19302'
        },
        {
            // 'url': 'turn:3.133.116.164:3478?transport=tcp',
            // 'username': 'adminsean',
            // 'credential': 'cruzrojaucsd'
            'url':`turn:${turnServer['host']}:${turnServer['port']}?transport=tcp`,
            'username': `${turnServer['username']}`,
            'credential': `${turnServer['password']}`
        }
    ]
} : {
    'iceServers': [{
        'urls': 'stun:stun.l.google.com:19302'
    }]
};

function maybeStart() {
    logger.log('debug', '>>>>>>> maybeStart(), turnServer = %j, isStarted = %s, localStream = %s, isChannelReady = %s',
        turnServer, isStarted, localStream, isChannelReady);
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
        pc = new RTCPeerConnection(pcConfig);
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
    logger.log('info', 'Looking for TURN server.');
    for (const i in pcConfig.iceServers) {
        if (pcConfig.iceServers[i].url.substr(0, 5) === 'turn:') {
            logger.log('info', "Setting up turn server '%j'", pcConfig.iceServers[i]);
            turnExists = true;
            turnReady = true;
            break;
        }
    }
    if (!turnExists && turnURL !== null) {
        logger.log('info', 'Getting TURN server from %s', turnURL);
        // No TURN server. Get one from computeengineondemand.appspot.com:
        const xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                const turnServer = JSON.parse(xhr.responseText);
                logger.log('info', 'Got TURN server from %s', turnServer);
                pcConfig.iceServers.push({
                    'url': 'turn:' + turnServer.username + '@' + turnServer.turn,
                    'credential': turnServer.password
                });
                turnReady = true;
            }
        };
        xhr.open('GET', turnURL, true);
        xhr.send();
    }
    if (!turnReady) {
        logger.log('warning', 'Could not find TURN server');
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
    sendMessage(remoteClient, {type: 'bye'});
    stop();
}

function handleRemoteHangup() {
    logger.log('info', 'Session terminated.');
    sendMessage(remoteClient, {type: 'bye'});
    stop();
    isInitiator = false;
}

/* stream: MediaStream, type:trackType('audio'/'video') */
function enableTrack(stream, enabled, type=null) {
    stream.getTracks().forEach((track) => {
        if (type === null || track.kind === type) {
            track.enabled = enabled;
        }
    });
}

function stop() {
    isStarted = false;
    isInitiator = false;
    state = State.IDLE;

    // disable tracks first
    if (typeof localStream !== 'undefined') {
        enableTrack(localStream, false);
    }

    pc.close();
    pc = null;
    modalReset();
}

function modalReset() {
    remoteClient = null;
    remoteClientText.empty();
    callButton.prop('disabled', true);
    callButton
        .removeClass('btn-danger')
        .addClass('btn-success');
    // hangupButton.prop('disabled', true);
}

function modalAlert(body, title) {
    title |= ''

    let html = '<div class="alert alert-warning alert-dismissible fade show" role="alert">';

    // add title
    if (title === '')
        html += `<h4 class="alert-heading">${title}</h4>`;

    // add body
    html += body;

    html += `<button type="button" class="close" data-dismiss="alert" aria-label="Close">
    <span aria-hidden="true">&times;</span>
  </button>
</div>`;

    $('#videoAlert').append(html);
}