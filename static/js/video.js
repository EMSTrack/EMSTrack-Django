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

// initialization function
function init (client) {

    logger.log('info', '> video.js');

    // set apiClient
    apiClient = client;

    // signup for client webrtc updates
    logger.log('info', 'Signing up for client webrtc updates');
    apiClient.observe(`user/${username}/client/${clientId}/webrtc/offer`, (message) => {
        message = parseMessage(message);
        if (!isInitiator && !isStarted) {
            maybeStart();
        }
        pc.setRemoteDescription(new RTCSessionDescription(message));
        doAnswer();
    });

    apiClient.observe(`user/${username}/client/${clientId}/webrtc/answer`, (message) => {
        if (isStarted) {
            message = parseMessage(message);
            pc.setRemoteDescription(new RTCSessionDescription(message));
        } else
            logger.log('info', "answer received answer but haven't started yet");
    });

    apiClient.observe(`user/${username}/client/${clientId}/webrtc/candidate`, (message) => {
        if (isStarted) {
            message = parseMessage(message);
            const candidate = new RTCIceCandidate({
                sdpMLineIndex: message.label,
                candidate: message.candidate
            });
            pc.addIceCandidate(candidate);
        }
        else
            logger.log('info', "candidate received answer but haven't started yet");
    });
    /*
    apiClient.observe(`user/${username}/client/${clientId}/webrtc/bye`, (message) => {
        if (isStarted)
            handleRemoteHangup();
    });
     */

}

function sendMessage(peer, topic, message) {
    if (peer === null) {
        logger.log('info', 'cannot send message %s/%s without a peer', topic, message);
        return;
    }

    console.log('Client sending message: ', message);
    //socket.emit('message', message);
    apiClient.publish(`user/${peer.username}/client/${peer.clientId}/webrtc/${topic}`, JSON.stringify(message), 0, false);
}

function parseMessage(message) {
    //accepting only JSON messages
    logger.log('debug', "got message: %s", message);
    let data;
    try {
        data = JSON.parse(message);
    } catch (e) {
        console.log("Invalid JSON");
        data = {};
    }
    return data;
}

// setup local stream

function gotStream(stream) {
    console.log('Adding local stream.');
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

    console.log('Getting user media with constraints', constraints);

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
    console.log('>>>>>>> maybeStart() ', isStarted, localStream, isChannelReady);
    if (!isStarted && typeof localStream !== 'undefined' && isChannelReady) {
        console.log('>>>>>> creating peer connection');
        createPeerConnection();
        pc.addStream(localStream);
        isStarted = true;
        console.log('isInitiator', isInitiator);
        if (isInitiator) {
            doCall();
        }
    }
}

window.onbeforeunload = function() {
    // sendMessage('bye');
};

/////////////////////////////////////////////////////////

function createPeerConnection() {
    try {
        pc = new RTCPeerConnection(null);
        pc.onicecandidate = handleIceCandidate;
        pc.onaddstream = handleRemoteStreamAdded;
        pc.onremovestream = handleRemoteStreamRemoved;
        console.log('Created RTCPeerConnnection');
    } catch (e) {
        console.log('Failed to create PeerConnection, exception: ' + e.message);
        alert('Cannot create RTCPeerConnection object.');
    }
}

function handleIceCandidate(event) {
    console.log('icecandidate event: ', event);
    if (event.candidate) {
        sendMessage(peer, 'candidate', {
            type: 'candidate',
            label: event.candidate.sdpMLineIndex,
            id: event.candidate.sdpMid,
            candidate: event.candidate.candidate
        });
    } else {
        console.log('End of candidates.');
    }
}

function setLocalAndSendMessage(topic, sessionDescription) {
    pc.setLocalDescription(sessionDescription);
    console.log('setLocalAndSendMessage sending message', sessionDescription);
    sendMessage(peer, topic, sessionDescription);
}

function doCall() {
    console.log('Sending offer to peer');
    pc.createOffer()
        .then( function(offer) {
            setLocalAndSendMessage('offer', offer);
        })
        .catch( function(reason) {
            logger.log('error', 'createOffer() error: %s', reason);
        });
}

function doAnswer() {
    console.log('Sending answer to peer.');
    pc.createAnswer()
        .then( function(answer) {
            setLocalAndSendMessage('answer', answer);
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
    console.log('Remote stream added.');
    remoteStream = event.stream;
    remoteVideo.srcObject = remoteStream;
}

function handleRemoteStreamRemoved(event) {
    console.log('Remote stream removed. Event: ', event);
}

function hangup() {
    console.log('Hanging up.');
    stop();
    sendMessage('bye');
}

function handleRemoteHangup() {
    console.log('Session terminated.');
    stop();
    isInitiator = false;
}

function stop() {
    isStarted = false;
    pc.close();
    pc = null;
}
