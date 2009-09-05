#!/usr/bin/python

debug = False

import gtk, gtk.keysyms, math, sys

class vector(tuple):
  __slots__ = ()

  def __new__(self, x=0, y=0):
    if hasattr(x, "__iter__"):
      if len(x) == 2:
         return tuple.__new__(self, x)
      else:
        raise AttributeError
    else:
      return tuple.__new__(self, (x, y))

  def __getattr__(self, name):
    if name == "x":
      return self[0]
    elif name == "y":
      return self[1]
    else:
      raise AttributeError
  
  def __add__(self, other):
    return vector((self.x + other.x, self.y + other.y))

  def __sub__(self, other):
    return vector((self.x - other.x, self.y - other.y))

  def __repr__(self):
    return "vector(x = %s, y = %s)" % (self.x, self.y)

class area(object):
  def __init__(self, *args):
    if type(args[0]) == type(args[1]) == vector:
      self.topleft = args[0]
      self.right = args[1].x
      self.bottom = args[1].y
    else:
      raise AttributeError

  def set_topleft(self, topleft):
    self.left = topleft.x
    self.top = topleft.y

  def get_topleft(self):
    return vector(self.left, self.top)

  topleft = property(get_topleft, set_topleft)

  def set_bottomright(self, bottomright):
    self.right = bottomright.x
    self.bottom = bottomright.y

  def get_bottomright(self):
    return vector(self.right, self.bottom)

  bottomright = property(get_bottomright, set_bottomright)

  def get_size(self):
    return self.bottomright - self.topleft

  def set_size(self, size):
    self.bottomright = self.topleft + size

  size = property(get_size, set_size)

  def __contains__(self, other):
    return self.left < other.x < self.right and self.top < other.y < self.bottom

  def move(self, movment):
    self.topleft += movment
    self.bottomright += movment

  def move_to(self, position):
    size = self.size
    self.topleft = position
    self.size = size
 
class element(object):
  def super(self):
    return super(self.__class__, self)

  def __init__(self, drawing_area, parent):
    self.drawing_area = drawing_area
    self.parent = parent

  def unselect_notify(self):
    pass
  
  def motion_notify(self, position):
    pass
  
  def button_press(self, position):
    self.drawing_area.select(self)
  
  def move(self, position):
    self.area.move(position)
  
  def key_press(self, keyval):
    self.parent.key_press(keyval)

  def draw_shadow(self, context):
    pass


class foobar(element):
  def i_elements(self):
    for i in self.elements:
      yield i

  def motion_notify(self, position):
    if self.drawing_area.selection == self and self.drawing_area.selection_on_mouse:
      self.move(position - self.drawing_area.mouse_position)
      self.drawing_area.redraw()
    for i in self.i_elements():
      i.motion_notify(position)

  def button_release(self, position):
    for i in self.i_elements():
      i.button_release(position)

  def in_chield_area(self, position):
    for i in self.i_elements():
      if i.in_area(position):
        return i
    return False

  def draw_shadow(self, context):
    self.draw_box(context, self.area.left + 3, self.area.top +3)
    context.set_source_rgba(0,0,0, 0.3)
    context.fill()
    for i in self.i_elements():
      i.draw_shadow(context)

  def draw(self, context):
    if debug:
      context.rectangle(self.area.left, self.area.top, 2, 2)
      context.set_source_rgb(1.0, .0, .0)
      context.fill()

    if self.drawing_area.selection == self:
      self.draw_shadow(context)
    self.draw_box(context, self.area.left, self.area.top)
    context.set_source_rgb(self.color[0], self.color[1], self.color[2])
    context.fill()
  
    for i in self.i_elements():
      i.draw(context)


  def move(self, position):
    self.area.move(position)
    for i in self.i_elements():
      i.move(position)
        
  def button_press(self, position):
    chield = self.in_chield_area(position)
    if chield:
      chield.button_press(position)
    else:
      self.drawing_area.select(self)
    self.drawing_area.redraw()
  
  
class container(foobar):
  def get_bad(self):
    raise AssertionError

  def set_bad(self, value):
    raise AssertionError

  position = property(get_bad, set_bad)
  size = property(get_bad, set_bad)

  def draw_box(self, context, x, y, r=16):
    w, h = self.area.size
    context.move_to(x, y+r)
    context.curve_to(x,y, x+r,y, x+r,y)
    context.line_to(x+w-r, y)
    context.curve_to(x+w,y, x+w,y+r, x+w,y+r)
    context.line_to(x+w, y+h-r)
    context.curve_to(x+w,y+h, x+w-r,y+h, x+w-r,y+h)
    context.line_to(x+r, y+h)
    context.curve_to(x,y+h, x,y+h-r, x,y+h-r)
    context.close_path()

class text(element):
  def __init__(self, drawing_area, parent, position):
    self.super().__init__(drawing_area, parent)
    self.text = u""

    context = self.drawing_area.window.cairo_create()
    textlayout = context.create_layout()
    textlayout.set_font_description(self.drawing_area.get_style().font_desc)
    textlayout.set_text(self.text)
    s = vector(textlayout.get_pixel_size())
    self.area = area(position, position + vector(12, 12))
    self.area.size += s

  def update_area(self):
    context = self.drawing_area.window.cairo_create()
    textlayout = context.create_layout()
    textlayout.set_font_description(self.drawing_area.get_style().font_desc)
    textlayout.set_text(self.text)
    self.area.size = vector(textlayout.get_pixel_size()) + vector(12, 12)

  def draw(self, context):
    if debug:
      context.rectangle(self.area.left, self.area.top, 2, 2)
      context.set_source_rgb(1.0, 1.0, .0)
      context.fill()
      context.rectangle(self.area.right, self.area.bottom, 2, 2)
      context.set_source_rgb(.0, 1.0, .0)
      context.fill()

    textlayout = context.create_layout()
    textlayout.set_font_description(self.drawing_area.get_style().font_desc)
    textlayout.set_text(self.text)
    if self.drawing_area.selection == self:
      context.rectangle(self.area.left, self.area.top, self.area.size.x, self.area.size.y)
      context.set_source_rgba(0,0,0,0.1)
      context.fill()

    context.move_to(self.area.left + 6, self.area.top + 6)
    context.set_source_rgb(.0, .0, .0)
    context.show_layout(textlayout)
    
  def in_area(self, position):
    return position in self.area

  def button_release(self, position):
    pass

  def key_press(self, keyval):
    if 31 < keyval < 256:
      self.text += chr(keyval).decode("latin-1")
    elif keyval == gtk.keysyms.BackSpace:
      self.text = self.text[:-1]
    else:
      self.parent.key_press(keyval)
      return
    self.update_area()
    self.parent.area_change_notify()
    self.drawing_area.redraw()

  def move_to(self, position):
    self.position = position
    self.area.move_to(position)
    
class parameter(foobar):
  def __init__(self, drawing_area, parent, position):
    super(parameter, self).__init__(drawing_area, parent)
    self.position = position
    self.name = text(drawing_area, self, self.position + vector(26, 0))
    self.area = area(self.position, self.position + vector(32, 32))
    self.color = (1.0, .8, .0)
    self.arrow = None

  def draw_shadow(self, context):
    self.draw_box(context, self.position.x + 3, self.position.y +3)
    context.set_source_rgba(0,0,0, 0.3)
    context.fill()
    for i in self.i_elements():
      i.draw_shadow(context)

  def draw_box(self, context, x, y, r=10):
    x += 6
    y += 6
    context.move_to(x, y+r)
    context.curve_to(x,y, x+r,y, x+r,y)
    context.curve_to(x+r*2,y, x+r*2,y+r, x+r*2,y+r)
    context.curve_to(x+r*2,y+r*2, x+r,y+r*2, x+r,y+r*2)
    context.curve_to(x,y+r*2, x,y+r, x,y+r)
    context.close_path()
 
  def i_elements(self):
    yield self.name

  def in_area(self, position):
    x, y = position
    return (self.position.x < x < self.position.x + 32 and self.position.y < y < self.position.y + 32) or self.in_chield_area(position)
  
  def move_to(self, position):
    self.move(position - self.position - vector(x = 16))
  
  def move(self, position):
    self.position += position
    self.area.move(position)
    for i in self.i_elements():
      i.move(position)
      
  def button_release(self, position):
    self.parent.area_change_notify()

  def targeted_notify(self, arrow):
    if self.arrow:
      self.arrow.parent.delete_arrow()
    self.arrow = arrow

  def untargeted_notify(self):
    self.arrow = None

  def area_change_notify(self):
    self.parent.area_change_notify()
        
class attribute(parameter):
  def __init__(self, drawing_area, parent, position):
    super(attribute, self).__init__(drawing_area, parent, position)
    self.name = text(drawing_area, self, self.position - vector(6, 0))
    self.area = area(self.position, self.position + vector(32, 32))
    self.color = (.0, .6, .0)

  def area_change_notify(self):
    self.name.move(vector(6 + self.position.x - self.name.area.right, 0))
    self.parent.area_change_notify()
      
  def key_press(self, keyval):
    if keyval == gtk.keysyms.less:
      if self.arrow:
        if self.arrow.target:
          self.arrow.target.untargeted_notify()
        self.arrow = None
      self.arrow = arrow(self.drawing_area, self, self.drawing_area.mouse_position)
      self.drawing_area.select(self.arrow)
      self.drawing_area.selection_on_mouse = True
      self.drawing_area.redraw()
    else:
      self.parent.key_press(keyval)

  def i_elements(self):
    yield self.name
    if self.arrow:
      yield self.arrow
     
  def delete_arrow(self):
    self.arrow = None


class arrow(element):
  def __init__(self, drawing_area, parent, target_position):
    self.super().__init__(drawing_area, parent)
    self.target_position = target_position
    self.target = None

  def draw(self, context):
    origin = self.parent.position + vector(16, 16)
    context.move_to(origin.x, origin.y)
    if self.target:
      context.line_to(self.target.position.x + 16, self.target.position.y + 16)
    else:
      context.line_to(self.target_position.x, self.target_position.y)
    context.close_path()
    context.set_source_rgb(.0, .0, .0)
    context.stroke()
   
  def in_area(self, position):
    return False
  
  def move(self, position):
    pass

  def motion_notify(self, position):
    if self.drawing_area.selection == self:
      self.target_position = position
      self.drawing_area.redraw()
  
  def unselect_notify(self):
    for i in self.parent.parent.i_parameters():
      if i.in_area(self.target_position):
        self.target = i
	self.target.targeted_notify(self)
	return
    self.parent.delete_arrow()
      

class call(container):
  def __init__(self, drawing_area, parent, position):
    super(call, self).__init__(drawing_area, parent)
    self.area = area(position, position + vector(32, 32))
    self.name = text(self.drawing_area, self, self.area.topleft)
    self.attributes = []
    self.parameters = []
    self.color = (0.9, 0.6, 0.1)

  def i_parameters(self):
    return self.parent.i_parameters()

  def i_elements(self):
    yield self.name
    for i in self.attributes:
      yield i
    for i in self.parameters:
      yield i
  
  def in_area(self, position):
    return position in self.area or self.in_chield_area(position)

  def move(self, position):
    self.area.move(position)
    for i in self.i_elements():
      i.move(position)
    self.parent.area_change_notify()

  def area_change_notify(self):
    top = sys.maxint
    bottom = 0

    for i in self.attributes + self.parameters:
      top = min(top, i.area.top)
      bottom = max(bottom, i.area.bottom)

    if len(self.attributes) + len(self.parameters) > 0:
      top -= 32
      self.area.top = top
      self.area.bottom = bottom

    self.name.move_to(self.area.topleft)

    width = 0

    for i in self.parameters:
      i.move_to(vector(self.area.left, i.position.y))
      for j in self.attributes:
        if i.name.area.top < j.name.area.top < i.name.area.bottom or j.name.area.top < i.name.area.top < j.name.area.bottom:
          width = max(width, i.name.area.size.x + j.name.area.size.x)
      width = max(width, i.name.area.size.x)
    
    for i in self.attributes:
      width = max(width, i.name.area.size.x)

    self.area.size = vector(max(self.name.area.size.x, 32 + width), self.area.size.y)

    for i in self.attributes:
      i.move_to(vector(self.area.right, i.position.y))

    self.parent.area_change_notify()

  def key_press(self, keyval):
    if keyval in (gtk.keysyms.Control_L, gtk.keysyms.Control_R):
      self.parameters.append(parameter(self.drawing_area, self, vector(self.area.left - 16, self.drawing_area.mouse_position.y)))
      self.area_change_notify()
      self.drawing_area.select(self.parameters[-1])
    elif keyval in (gtk.keysyms.Alt_L, gtk.keysyms.Alt_R):
      self.attributes.append(attribute(self.drawing_area, self, vector(self.area.right - 16, self.drawing_area.mouse_position.y)))
      self.area_change_notify()
      self.drawing_area.select(self.attributes[-1])
    else:
      self.parent.key_press(keyval)
      return
    self.drawing_area.redraw()

class string(call):
  def __init__(self, drawing_area, parent, position):
    self.super().__init__(drawing_area, parent, position)
    self.color = (.8, .3, .2)

class function(container):
  def __init__(self, drawing_area, parent, position):
    self.super().__init__(drawing_area, parent)
    self.area = area(position, position + vector(32, 32))
    self.name = text(self.drawing_area, self, self.area.topleft)
    self.attributes = []
    self.parameters = []
    self.elements = []

  def i_elements(self):
    yield self.name
    for i in self.attributes:
      yield i
    for i in self.parameters:
      yield i
    for i in self.elements:
      yield i

  def i_parameters(self):
    for i in self.parameters:
      yield i
    for i in self.elements:
      for j in i.parameters:
        yield j

  def key_press(self, keyval):
    if keyval in (gtk.keysyms.Control_L, gtk.keysyms.Control_R):
      self.attributes.append(attribute(self.drawing_area, self, vector(self.area.left - 16, self.drawing_area.mouse_position.y)))
      self.area_change_notify()
      self.drawing_area.select(self.attributes[-1])
    elif keyval in (gtk.keysyms.Alt_L, gtk.keysyms.Alt_R):
      self.parameters.append(parameter(self.drawing_area, self, vector(self.area.right - 16, self.drawing_area.mouse_position.y)))
      self.area_change_notify()
      self.drawing_area.select(self.parameters[-1])
    elif keyval == gtk.keysyms.exclam:
      self.elements.append(call(self.drawing_area, self, self.drawing_area.mouse_position - vector(6,6)))
      self.drawing_area.select(self.elements[-1])
      self.drawing_area.selection_on_mouse = True
      self.area_change_notify()
    elif keyval == gtk.keysyms.quotedbl:
      self.elements.append(string(self.drawing_area, self, self.drawing_area.mouse_position - vector(6,6)))
      self.drawing_area.select(self.elements[-1])
      self.drawing_area.selection_on_mouse = True
      self.area_change_notify()
    else:
      self.parent.key_press(keyval)
      return
    self.drawing_area.redraw()

  def area_change_notify(self):
    if len(self.elements) > 0:
      left = sys.maxint
      top = sys.maxint
      right = 0
      bottom = 0
      for i in self.elements:
        left = min(left, i.area.left)
        top = min(top, i.area.top)
        right = max(right, i.area.right)
        bottom = max(bottom, i.area.bottom)

      left -= 32
      bottom += 16
      right += 32
    else:
      left = self.area.left
      top = self.area.top
      right = self.area.right
      bottom = self.area.bottom

    right = max(self.name.area.right, right)

    for i in self.attributes + self.parameters:
      top = min(top, i.area.top)
      bottom = max(bottom, i.area.bottom)

    if len(self.elements) > 0:
      top -= 32

    self.area.topleft = vector(left, top)
    self.area.bottomright = vector(right, bottom)

    self.name.move_to(self.area.topleft)
    for i in self.attributes:
      i.move_to(vector(self.area.left, i.position.y))

    for i in self.parameters:
      i.move_to(vector(self.area.right, i.position.y))

  def draw(self, context):
    if debug:
      context.rectangle(self.area.left, self.area.top, 2, 2)
      context.set_source_rgb(1.0, .0, .0)
      context.fill()

    if self.drawing_area.selection == self:
      self.draw_shadow(context)
    self.draw_box(context, self.area.left, self.area.top)
    context.set_source_rgb(188.0/255, 239.0/255, 245.0/255)
    context.fill()
    
    for i in self.i_elements():
      i.draw(context)
  

  def in_area(self, position):
    x, y = position
    return position in self.area or self.in_chield_area(position)


class root(foobar):
  def __init__(self, drawing_area):
    self.super().__init__(drawing_area, None)

    self.elements = []

  def delete(self, element):
    self.elements.remove(element)


  def draw(self, context):
    for i in self.elements:
      i.draw(context)

  def key_press(self, keyval):
    if keyval == gtk.keysyms.Escape:
      self.drawing_area.quit()
    elif keyval == gtk.keysyms.space:
      self.elements.append(function(self.drawing_area, self, self.drawing_area.mouse_position - vector(6,6)))
      self.drawing_area.select(self.elements[-1])
      self.drawing_area.selection_on_mouse = True
      self.drawing_area.redraw()

  def move(self, position):
    pass
  

class drawing_area(gtk.DrawingArea):
  def __init__(self):
    super(drawing_area, self).__init__()

    self.connect("expose_event", self.expose)
    self.connect("button_press_event", self.button_press)
    self.connect("button_release_event", self.button_release)
    self.connect("motion_notify_event", self.motion_notify)
    self.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK)

    window = gtk.Window()
    self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(65535, 65535, 65535))
    window.add(self)
    window.connect("destroy", gtk.main_quit)
    window.connect("key_press_event", self.key_press)
    window.connect("key_release_event", self.key_release)
    window.show_all()

    self.root = root(self)
    self.selection = self.root
    self.mouse_position = vector()
    self.selection_on_mouse = False
 
  def select(self, element):
    if not self.selection == element:
      self.selection.unselect_notify()
      self.selection = element

  def quit(self):
    gtk.main_quit()

  def motion_notify(self, widget, event):
    self.root.motion_notify(vector(event.x, event.y))
    self.mouse_position = vector(event.x, event.y)

  def button_press(self, widget, event):
    self.selection_on_mouse = True
    self.root.button_press(vector(event.x, event.y))
  
  def button_release(self, widget, event):
    self.selection_on_mouse = False
    self.root.button_release(vector(event.x, event.y))
    self.redraw()

  def key_press(self, widget, event):
    for i in gtk.keysyms.__dict__.iteritems():
      if i[1] == event.keyval:
        print i[0]
    self.selection.key_press(event.keyval)
  
  def key_release(self, widget, event):
    pass

  def expose(self, widget, event):
    context = widget.window.cairo_create()
    context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
    context.clip()
    context.set_line_width(1)
    self.width = event.area.width
    self.height = event.area.height
    self.draw(context)
    return False
  
  def redraw(self):
    if self.window:
      alloc = self.get_allocation()
      self.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)

  def draw(self, context):
    self.root.draw(context)

  def main(self):
    gtk.main()


drawing_area().main()
