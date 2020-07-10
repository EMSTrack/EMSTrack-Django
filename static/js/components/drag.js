

// Make an element draggable:
import {logger} from "../logger";

export function dragElement(elmnt, parent = null) {

    let diffX, diffY;
    // otherwise, move the DIV from anywhere inside the DIV:
    elmnt.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        // e = e || window.event;
        e.preventDefault();

        // get the mouse cursor position at startup:
        const posX = e.clientX,
              posY = e.clientY;

        // calculate diffs
        let divTop = elmnt.style.top,
            divLeft = elmnt.style.left;

        divLeft = divLeft.replace('px','');
        diffX = posX - divLeft;

        divTop = divTop.replace('px','');
        diffY = posY - divTop;

        logger.log('debug', 'diffX = %d, diffY = %d', diffX, diffY);

        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        // e = e || window.event;
        e.preventDefault();

        // calculate the new cursor position:
        const posX = e.clientX,
              posY = e.clientY,

              aX = posX - diffX,
              aY = posY - diffY;

        const bound = parent !== null ? parent.offsetWidth-elmnt.offsetWidth : 0;

        logger.log('debug', 'aX = %d, diffY = %d, bound = %d', aX, aY, bound);

        if (parent === null || ((aX>0)&&(aX<bound)&&(aY>0)&&(aY<bound))) {
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

}