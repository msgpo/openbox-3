############################################################################
###    Functions that provide callbacks for motion events to move and    ###
###    resize windows.                                                   ###
############################################################################

#############################################################################
### Options that can be modified to change the functions' behaviors.      ###
###                                                                       ###
# edge_resistance - the amount of resistance to provide to moving a       ###
###                 window past a screen boundary. Specify a value of 0   ###
###                 to disable edge resistance.                           ###
edge_resistance = 10                                                      ###
###                                                                       ###
# move_popup - display a coordinates popup when moving windows.           ###
move_popup = 1                                                            ###
###                                                                       ###
# NOT IMPLEMENTED (yet?)                                                  ###
# move_rubberband - display an outline while moving instead of moving the ###
###                 actual window, until the move is completed. Good for  ###
###                 slower systems.                                       ###
move_rubberband = 0                                                       ###
###                                                                       ###
# resize_popup - display a size popup when resizing windows.              ###
resize_popup = 1                                                          ###
###                                                                       ###
# NOT IMPLEMENTED (yet?)                                                  ###
# resize_rubberband - display an outline while resizing instead of        ###
###                   resizing the actual window, until the resize is     ###
###                   completed. Good for slower systems.                 ###
resize_rubberband = 0                                                     ###
###                                                                       ###
# resize_nearest - 1 to resize from the corner nearest where the mouse    ###
###                is, 0 to resize always from the bottom right corner.   ###
resize_nearest = 1                                                        ###
###                                                                       ###
###                                                                       ###
# Provides:                                                               ###
# def move(data):                                                         ###
#     """Moves the window interactively. This should only be used with    ###
#        MouseMotion events. If move_popup or move_rubberband is enabled, ###
#        then the end_move function needs to be bound as well."""         ###
# def end_move(data):                                                     ###
#     """Complete the interactive move of a window."""                    ###
# def resize(data):                                                       ###
#     """Resizes the window interactively. This should only be used with  ###
#        MouseMotion events"""                                            ###
# def end_resize(data):                                                   ###
#     """Complete the interactive resize of a window."""                  ###
###                                                                       ###
#############################################################################

import ob
import otk

_popwidget = 0
_poplabel = 0

# motion state
_inmove = 0
_inresize = 0

# last motion data
_cx = 0
_cy = 0
_cw = 0
_ch = 0
_px = 0
_py = 0
_dx = 0
_dy = 0
_client = 0
_screen = 0

_motion_mask = 0

def _motion_grab(data):
    global _motion_mask, _inmove, _inresize;

    if data.action == ob.KeyAction.Release:
        # have all the modifiers this started with been released?
        if not _motion_mask & data.state:
            if _inmove:
                end_move(data)
            elif _inresize:
                end_resize(data)
            else:
                raise RuntimeError

_last_x = 0
_last_y = 0

def _do_move():
    global _screen, _client, _cx, _cy, _dx, _dy

    # get destination x/y for the *frame*
    x = _cx + _dx + _client.frame.rect().x() - _client.area().x()
    y = _cy + _dy + _client.frame.rect().y() - _client.area().y()

    global edge_resistance
    global _last_x, _last_y
    if edge_resistance:
        fs = _client.frame.size()
        w = _client.area().width() + fs.left + fs.right
        h = _client.area().height() + fs.top + fs.bottom
        # use the area based on the struts
        area = ob.openbox.screen(_screen).area()
        l = area.left()
        r = area.right() - w + 1
        t = area.top()
        b = area.bottom() - h + 1
        # left screen edge
        if _last_x > x and x < l and x >= l - edge_resistance:
            x = l
        # right screen edge
        if _last_x < x and x > r and x <= r + edge_resistance:
            x = r
        # top screen edge
        if _last_y > y and y < t and y >= t - edge_resistance:
            y = t
        # right screen edge
        if _last_y < y and y > b and y <= b + edge_resistance:
            y = b

    global _inmove
    if not _inmove:
        _last_x = 0
        _last_y = 0
    else:
        _last_x = x
        _last_y = y

    global move_rubberband
    if move_rubberband:
        # draw the outline ...
        f=0
    else:
        print "moving " + str(x) + " " + str(y)
        _client.move(x, y, 1) # move the *frame*

    global move_popup
    if move_popup:
        global _popwidget, _poplabel
        style = ob.openbox.screen(_screen).style()
        font = style.labelFont()
        text = "X: " + str(x) + " Y: " + str(y)
        length = font.measureString(text)
        if not _popwidget:
            _popwidget = otk.Widget(ob.openbox, style,
                                    otk.Widget.Horizontal, 0,
                                    style.bevelWidth(), 1)
            _popwidget.setTexture(style.titlebarFocusBackground())
            _poplabel = otk.Label(_popwidget)
            _poplabel.setTexture(style.labelFocusBackground())
        _poplabel.fitString(text)
        _poplabel.setText(text)
        _popwidget.update() 
        area = otk.display.screenInfo(_screen).rect()
        _popwidget.move(area.x() + (area.width() -
                                    _popwidget.width()) / 2,
                        area.y() + (area.height() -
                                    _popwidget.height()) / 2)
        _popwidget.show(1)

def move(data):
    """Moves the window interactively. This should only be used with
       MouseMotion events. If move_popup or move_rubberband is enabled, then
       the end_move function needs to be bound as well."""
    if not data.client: return

    # not-normal windows dont get moved
    if not data.client.normal(): return

    global _screen, _client, _cx, _cy, _dx, _dy
    _screen = data.screen
    _client = data.client
    _cx = data.press_clientx
    _cy = data.press_clienty
    _dx = data.xroot - data.pressx
    _dy = data.yroot - data.pressy
    _do_move()
    global _inmove
    if not _inmove:
        ob.kgrab(_screen, _motion_grab)
        _inmove = 1

def end_move(data):
    """Complete the interactive move of a window."""
    global move_rubberband, _inmove
    global _popwidget, _poplabel
    if _inmove:
        r = move_rubberband
        move_rubberband = 0
        _do_move()
        move_rubberband = r
        _inmove = 0
    _poplabel = 0
    _popwidget = 0
    ob.kungrab()

def _do_resize():
    global _screen, _client, _cx, _cy, _cw, _ch, _px, _py, _dx, _dy

    dx = _dx
    dy = _dy
    
    # pick a corner to anchor
    if not (resize_nearest or _context == ob.MouseContext.Grip):
        corner = ob.Client.TopLeft
    else:
        x = _px - _cx
        y = _py - _cy
        if y < _ch / 2:
            if x < _cw / 2:
                corner = ob.Client.BottomRight
                dx *= -1
            else:
                corner = ob.Client.BottomLeft
            dy *= -1
        else:
            if x < _cw / 2:
                corner = ob.Client.TopRight
                dx *= -1
            else:
                corner = ob.Client.TopLeft

    w = _cw + dx
    h = _ch + dy

    global resize_popup
    if resize_rubberband:
        # draw the outline ...
        f=0
    else:
        _client.resize(corner, w, h)

    global resize_popup
    if resize_popup:
        global _popwidget, _poplabel
        style = ob.openbox.screen(_screen).style()
        ls = _client.logicalSize()
        text = "W: " + str(ls.x()) + " H: " + str(ls.y())
        if not _popwidget:
            _popwidget = otk.Widget(ob.openbox, style,
                                    otk.Widget.Horizontal, 0,
                                    style.bevelWidth(), 1)
            _popwidget.setTexture(style.titlebarFocusBackground())
            _poplabel = otk.Label(_popwidget)
            _poplabel.setTexture(style.labelFocusBackground())
        _poplabel.fitString(text)
        _poplabel.setText(text)
        area = otk.display.screenInfo(_screen).rect()
        _popwidget.update() 
        _popwidget.move(area.x() + (area.width() -
                                    _popwidget.width()) / 2,
                        area.y() + (area.height() -
                                    _popwidget.height()) / 2)
        _popwidget.show(1)

def resize(data):
    """Resizes the window interactively. This should only be used with
       MouseMotion events"""
    if not data.client: return

    # not-normal windows dont get resized
    if not data.client.normal(): return

    global _screen, _client, _cx, _cy, _cw, _ch, _px, _py, _dx, _dy
    _screen = data.screen
    _client = data.client
    _cx = data.press_clientx
    _cy = data.press_clienty
    _cw = data.press_clientwidth
    _ch = data.press_clientheight
    _px = data.pressx
    _py = data.pressy
    _dx = data.xroot - _px
    _dy = data.yroot - _py
    _do_resize()
    global _inresize
    if not _inresize:
        ob.kgrab(_screen, _motion_grab)
        _inresize = 1

def end_resize(data):
    """Complete the interactive resize of a window."""
    global resize_rubberband, _inresize
    global _popwidget, _poplabel
    if _inresize:
        r = resize_rubberband
        resize_rubberband = 0
        _do_resize()
        resize_rubberband = r
        _inresize = 0
    _poplabel = 0
    _popwidget = 0
    ob.kungrab()
