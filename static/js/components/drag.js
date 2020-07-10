

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

        const bbox = elmnt.getBoundingClientRect();
        const shiftX = e.clientX - bbox.left;
        const shiftY = e.clientY - bbox.top;

        moveAt(e.clientX, e.clientY);

        function moveAt(pageX, pageY) {
            elmnt.style.left = pageX - shiftX + 'px';
            elmnt.style.top = pageY - shiftY + 'px';
        }

        function onMouseMove(event) {
            moveAt(event.clientX, event.clientY);
        }

        function onMouseUp() {
            document.onmouseup = null;
            document.onmousemove = null;
        }

        // move the ball on mousemove
        document.onmousemove = onMouseMove;
        document.onmouseup = onMouseUp;

        // drop the ball, remove unneeded handlers
        elmnt.onmouseup = function () {
            document.removeEventListener('mousemove', onMouseMove);
            elmnt.onmouseup = null;
        };

    }


        /*
        // get the mouse cursor position at startup:
        const posX = e.clientX,
              posY = e.clientY;

        // calculate dX and dY
        if (parent !== null) {

            const offsets = parent.getBoundingClientRect();
            parentTop = offsets.top;
            parentLeft = offsets.left;

            boundX = parent.offsetWidth - elmnt.offsetWidth;
            boundY = parent.offsetHeight - elmnt.offsetHeight;

        }

        dX = posX - parentLeft - elmnt.style.left.replace('px','');
        dY = posY - parentTop - elmnt.style.top.replace('px','');

        logger.log('debug', 'dX = %d, dY = %d, parentTop = %d, parentLeft = %d, boundX = %d, boundY = %d',
            dX, dY, parentTop, parentLeft, boundX, boundY);

        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        // e = e || window.event;
        e.preventDefault();

        // calculate the new cursor position:
        const posX = e.clientX,
              posY = e.clientY,

              aX = posX - dX,
              aY = posY - dY;

        logger.log('debug', 'aX = %d, aY = %d', aX, aY);

        if (parent === null ||
            ((aX>parentLeft) && (aX<parentLeft+boundX) &&
                (aY>parentTop) && (aY<parentTop+boundY))) {
            // set the element's new position:
            elmnt.style.left = aX + "px";
            elmnt.style.top = aY + "px";
        }
    }

    function closeDragElement() {
        // stop moving when mouse button is released:
        document.onmouseup = null;
        document.onmousemove = null;
    }

         */

}