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
let peer;

let onlineClients;

// initialization function
function init (client) {

    logger.log('info', '> video.js');

    // set apiClient
    apiClient = client;

    // retrieve online clients
    retrieveOnlineClients();

    // signup for client webrtc updates
    logger.log('info', 'Signing up for client webrtc updates');
    apiClient.subscribeToWebRTC((message) => {
        message = parseMessage(message);
        if (message.type === 'offer') {
            if (!isInitiator && !isStarted) {
                maybeStart();
            }
            pc.setRemoteDescription(new RTCSessionDescription(message));
            doAnswer();
        } else if (message.type === 'answer' && isStarted) {
            pc.setRemoteDescription(new RTCSessionDescription(message));
        } else if (message.type === 'candidate' && isStarted) {
            const candidate = new RTCIceCandidate({
                sdpMLineIndex: message.label,
                candidate: message.candidate
            });
            pc.addIceCandidate(candidate);
        } else if (message.type === 'bye' && isStarted) {
            handleRemoteHangup();
        }
    });

    // set channel as ready
    isChannelReady = true;

}

// Ready function
$(function () {

});

function retrieveOnlineClients() {
    apiClient.getClients()
        .then( (clients) => {
            logger.log('info', '%d clients retrieved', Object.keys(clients).length);
            onlineClients = clients;
            const dropdown = $('#clients-dropdown');
            dropdown.empty();
            for (const client of onlineClients) {
                if (client.client_id !== clientId) {
                    const html = `<a class="dropdown-item" href="#" id="${client.username}_${client.client_id}">${client.username} @ ${client.client_id}</a>`;
                    dropdown.append(html);
                    $(`#${client.username}_${client.client_id}`).click(function() {
                        if (!isStarted) {
                            peer = client;
                            isInitiator = true;
                            maybeStart();
                        }
                        // TODO: not possible to start if already started
                    });

                }
            }
        })
        .catch( (error) => {
            logger.log('error', 'Failed to retrieve clients from ApiClient: %j', error);
        })
}

function sendMessage(peer, message) {
    if (peer === null) {
        logger.log('info', 'cannot send message %j without a peer', message);
        return;
    }

    logger.log('info', 'Client sending message: %j', message);
    //socket.emit('message', message);
    apiClient.publish(`user/${peer.username}/client/${peer.client_id}/webrtc/message`, JSON.stringify(message), 0, false);
}

function parseMessage(message) {
    //accepting only JSON messages
    logger.log('debug', "got message: %s", message);
    console.log(message);
    let data;
    try {
        data = JSON.parse(message);
    } catch (e) {
        logger.log('error', "Invalid JSON '%s'", message);
        data = {};
    }
    return data;
}

// setup local stream

function gotStream(stream) {
    logger.log('info', 'Adding local stream.');
    localStream = stream;
    localVideo.srcObject = stream;
    // sendMessage('got user media');
    if (isInitiator) {
        maybeStart();
    }
}

$(function () {

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

    if (location.hostname !== 'localhost') {
        requestTurn(
            'https://computeengineondemand.appspot.com/turn?username=41784574&key=4080218913'
        );
    }

})

const pcConfig = {
    'iceServers': [{
        'urls': 'stun:stun.l.google.com:19302'
    }]
};

// Set up audio and video regardless of what devices are present.
const sdpConstraints = {
    offerToReceiveAudio: true,
    offerToReceiveVideo: true
};

/////////////////////////////////////////////

const room = 'foo';
// Could prompt for room name:
// room = prompt('Enter room name:');

/*
var socket = io.connect();

if (room !== '') {
  socket.emit('create or join', room);
  console.log('Attempted to create or  join room', room);
}

socket.on('created', function(room) {
  console.log('Created room ' + room);
  isInitiator = true;
});

socket.on('full', function(room) {
  console.log('Room ' + room + ' is full');
});

socket.on('join', function (room){
  console.log('Another peer made a request to join room ' + room);
  console.log('This peer is the initiator of room ' + room + '!');
  isChannelReady = true;
});

socket.on('joined', function(room) {
  console.log('joined: ' + room);
  isChannelReady = true;
});

socket.on('log', function(array) {
  console.log.apply(console, array);
});
*/

////////////////////////////////////////////////

/*
// This client receives a message
socket.on('message', function(message) {
    console.log('Client received message:', message);
    if (message === 'got user media') {
        maybeStart();
    } else if (message.type === 'offer') {
        if (!isInitiator && !isStarted) {
            maybeStart();
        }
        pc.setRemoteDescription(new RTCSessionDescription(message));
        doAnswer();
    } else if (message.type === 'answer' && isStarted) {
        pc.setRemoteDescription(new RTCSessionDescription(message));
    } else if (message.type === 'candidate' && isStarted) {
        var candidate = new RTCIceCandidate({
            sdpMLineIndex: message.label,
            candidate: message.candidate
        });
        pc.addIceCandidate(candidate);
    } else if (message === 'bye' && isStarted) {
        handleRemoteHangup();
    }
});
*/

////////////////////////////////////////////////////

function maybeStart() {
    logger.log('debug', '>>>>>>> maybeStart() ', isStarted, localStream, isChannelReady);
    if (!isStarted && typeof localStream !== 'undefined' && isChannelReady) {
        logger.log('info', 'creating peer connection');
        createPeerConnection();
        pc.addStream(localStream);
        isStarted = true;
        logger.log('debug', 'isInitiator = %s', isInitiator);
        if (isInitiator) {
            doCall();
        }
    }
}

window.onbeforeunload = function() {
    sendMessage(peer, {type: 'bye'});
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
        sendMessage(peer, {
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
    sendMessage(peer, sessionDescription);
}

function doCall() {
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
    sendMessage(peer, {type: 'bye'});
}

function handleRemoteHangup() {
    logger.log('info', 'Session terminated.');
    stop();
    isInitiator = false;
}

function stop() {
    isStarted = false;
    pc.close();
    pc = null;
}
