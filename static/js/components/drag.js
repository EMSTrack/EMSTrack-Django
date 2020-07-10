

// Make an element draggable:
import {logger} from "../logger";

export function dragElement(elmnt, parent = null) {

    let dX, dY;
    let parentTop, parentLeft;
    // otherwise, move the DIV from anywhere inside the DIV:
    elmnt.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        // e = e || window.event;
        e.preventDefault();

        // get the mouse cursor position at startup:
        const posX = e.clientX,
              posY = e.clientY;

        // calculate diffs
        let elmntTop = elmnt.style.top,
            elmntLeft = elmnt.style.left;

        parentTop = parent !== null ? parent.style.top : 0;
        parentLeft = parent !== null ? parent.style.left : 0;

        elmntLeft = elmntLeft.replace('px','');
        dX = posX - elmntLeft;

        elmntTop = elmntTop.replace('px','');
        dY = posY - elmntTop;

        logger.log('debug', 'dX = %d, dY = %d, parentTop = %d, parentLeft = %d',
            dX, dY, parentTop, parentLeft);

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

        const boundX = parent !== null ? parent.offsetWidth - elmnt.offsetWidth : 0;
        const boundY = parent !== null ? parent.offsetHeight - elmnt.offsetHeight : 0;

        logger.log('debug', 'aX = %d, aY = %d, boundX = %d, boundY = %d', aX, aY, boundX, boundY);

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

}