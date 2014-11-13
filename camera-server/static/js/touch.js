function setEvent($element, down, move, up) {
    $element.mousedown(down);
    $element.mousemove(move);
    $element.mouseup(up);
    $element.bind("touchstart", down);
    $element.bind("touchmove", move);
    $element.bind("touchend", up);
}
