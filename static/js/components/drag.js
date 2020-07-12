// Make an element draggable:
import {logger} from "../logger";

export function dragElement(elmnt, parent = null) {

    let dX, dY;
    let parentTop = 0, parentLeft = 0, boundX = 0, boundY = 0;

    elmnt.ondragstart = function() {
        return false;
    };

    elmnt.onmousedown = function dragMouseDown(e) {
        // e = e || window.event;
        e.preventDefault();

        if (parent !== null) {

            const bbox = parent.getBoundingClientRect();
            parentTop = bbox.top;
            parentLeft = bbox.left;

            boundX = parent.offsetWidth - elmnt.offsetWidth;
            boundY = parent.offsetHeight - elmnt.offsetHeight;

        }

        const bbox = elmnt.getBoundingClientRect();
        const shiftX = e.clientX - bbox.left + parentLeft;
        const shiftY = e.clientY - bbox.top + parentTop;

        moveAt(e.clientX, e.clientY);

        function moveAt(pageX, pageY) {
            elmnt.style.left = pageX - shiftX + 'px';
            elmnt.style.top = pageY - shiftY + 'px';
        }

        function onMouseMove(event) {
            let aX = event.clientX, aY = event.clientY;
            if (parent !== null) {

                // horizontal constraints
                if ( aX - shiftX < 0 )
                    aX = shiftX;
                else if ( aX - shiftX > boundX )
                    aX = shiftX + boundX;

                // vertical constraints
                if ( aY - shiftY < 0 )
                    aY = shiftY;
                else if ( aY -shiftY > boundY )
                    aY = shiftY + boundY;

            }
            moveAt(aX, aY);
        }

        function onMouseUp() {
            document.onmouseup = null;
            document.onmousemove = null;
        }

        // move the ball on mousemove
        document.onmousemove = onMouseMove;
        document.onmouseup = onMouseUp;

    }

}