import { logger } from './logger';

let apiClient;

// add initialization hook
add_init_function(init);

// initialization function
function init (client) {

    logger.log('info', '> video.js');

    // set apiClient
    apiClient = client;

}

let RTCConnection;
let localStream;

// Video element where stream will be placed.
const localVideo = document.querySelector('localVideo');
const remoteVideo = document.querySelector('remoteVideo');

// Handles success by adding the MediaStream to the video element.
function gotLocalMediaStream(mediaStream) {
    localStream = mediaStream;
    localVideo.srcObject = mediaStream;
}

function setupRTC() {

    //using Google public stun server
    const configuration = {
        "iceServers": [{"url": "stun:stun2.1.google.com:19302"}]
    };
    RTCConnection = new webkitRTCPeerConnection(configuration);

    // setup stream listening
    RTCConnection.addStream(localStream);

    //when a remote user adds stream to the peer connection, we display it
    RTCConnection.onaddstream = function (e) {
        remoteVideo.srcObject = e.stream;
    };

    // Setup ice handling
    RTCConnection.onicecandidate = function (event) {
        if (event.candidate) {
            send({
                type: "candidate",
                candidate: event.candidate
            });
        }
    };

}

// Handles error by logging a message to the console with the error message.
function handleLocalMediaStreamError(error) {
    console.log('navigator.getUserMedia error: ', error);
}

$(function () {

    //**********************
    //Starting a peer connection
    //**********************
    // https://www.tutorialspoint.com/webrtc/webrtc_video_demo.htm

    // On this codelab, you will be streaming only video (video: true).
    const mediaStreamConstraints = {
        video: true,
        audio: true,
    };

    // Initializes media stream.
    navigator.mediaDevices.getUserMedia(mediaStreamConstraints)
        .then(gotLocalMediaStream)
        .then(setupRTC)
        .catch(handleLocalMediaStreamError);

})
