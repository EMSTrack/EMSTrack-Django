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

let yourConn;
let stream;

$(function () {

    const localVideo = $('#localVideo');
    const remoteVideo = $('#remoteVideo');

    //**********************
    //Starting a peer connection
    //**********************
    // https://www.tutorialspoint.com/webrtc/webrtc_video_demo.htm

    //getting local video stream
    navigator.webkitGetUserMedia({ video: true, audio: true }, function (myStream) {
        stream = myStream;

        //displaying local video stream on the page
        localVideo.src = window.URL.createObjectURL(stream);

        //using Google public stun server
        var configuration = {
            "iceServers": [{ "url": "stun:stun2.1.google.com:19302" }]
        };

        yourConn = new webkitRTCPeerConnection(configuration);

        // setup stream listening
        yourConn.addStream(stream);

        //when a remote user adds stream to the peer connection, we display it
        yourConn.onaddstream = function (e) {
            remoteVideo.src = window.URL.createObjectURL(e.stream);
        };

        // Setup ice handling
        yourConn.onicecandidate = function (event) {
            if (event.candidate) {
                send({
                    type: "candidate",
                    candidate: event.candidate
                });
            }
        };

    }, function (error) {
        console.log(error);
    });

})
