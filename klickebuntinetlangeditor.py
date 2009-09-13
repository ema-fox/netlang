#!/usr/bin/python

debug = False

import gtk, gtk.keysyms, math, sys, pickle

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
  
  def get_width(self):
    return self.right - self.left

  def get_height(self):
    return self.bottom - self.top

  width = property(get_width)
  height = property(get_height)

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
  def unselect_notify(self):
    pass
  
  def motion_notify(self, position):
    pass
  
  def button_press(self, position):
    select(self)
  
  def key_press(self, keyval):
    self.parent.key_press(keyval)

  def draw_shadow(self, context):
    pass


class foobar(element):
  def all_elements(self):
    for i in self.elements:
      yield i

  def motion_notify(self, position):
    if selection == self and selection_on_mouse:
      self.move(position - mouse_position)
      redraw()
    for i in self.all_elements():
      i.motion_notify(position)

  def button_release(self, position):
    for i in self.all_elements():
      i.button_release(position)

  def in_chield_area(self, position):
    for i in self.all_elements():
      if i.in_area(position):
        return i
    return False

  def draw_shadow(self, context):
    self.draw_box(context, self.area.left + 3, self.area.top +3)
    context.set_source_rgba(0,0,0, 0.3)
    context.fill()
    for i in self.all_elements():
      i.draw_shadow(context)

  def draw(self, context):
    if debug:
      context.rectangle(self.area.left, self.area.top, 2, 2)
      context.set_source_rgb(1.0, .0, .0)
      context.fill()

    if selection == self:
      self.draw_shadow(context)
    self.draw_box(context, self.area.left, self.area.top)
    context.set_source_rgb(self.color[0], self.color[1], self.color[2])
    context.fill()
  
    for i in self.draw_elements():
      i.draw(context)


  def move(self, position):
    self.area.move(position)
    for i in self.all_elements():
      i.move(position)
        
  def button_press(self, position):
    chield = self.in_chield_area(position)
    if chield:
      chield.button_press(position)
    else:
      select(self)
    redraw()
  
  
class container(foobar):
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
  def __init__(self, parent, position):
    self.parent = parent
    self.text = u""

    context = drawing_area.window.cairo_create()
    textlayout = context.create_layout()
    textlayout.set_font_description(drawing_area.get_style().font_desc)
    textlayout.set_text(self.text)
    s = vector(textlayout.get_pixel_size())
    self.area = area(position, position + vector(12, 12))
    self.area.size += s

  def update_area(self):
    context = drawing_area.window.cairo_create()
    textlayout = context.create_layout()
    textlayout.set_font_description(drawing_area.get_style().font_desc)
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
    textlayout.set_font_description(drawing_area.get_style().font_desc)
    textlayout.set_text(self.text)
    if selection == self:
      context.rectangle(self.area.left, self.area.top, self.area.size.x, self.area.size.y)
      context.set_source_rgba(0,0,0,0.1)
      context.fill()

    context.move_to(self.area.left + 6, self.area.top + 6)
    context.set_source_rgb(.0, .0, .0)
    context.show_layout(textlayout)
    
  def move(self, position):
    self.area.move(position)
  
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
    redraw()

  def move_to(self, position):
    self.position = position
    self.area.move_to(position)
    
class parameter(foobar):
  def __init__(self, parent, position):
    self.parent = parent
    self.position = position
    self.name = text(self, self.position + vector(26, 0))
    self.area = area(self.position, self.position + vector(32, 32))
    self.color = (1.0, .8, .0)
    self.target_arrow = None

  def draw_shadow(self, context):
    self.draw_box(context, self.position.x + 3, self.position.y +3)
    context.set_source_rgba(0,0,0, 0.3)
    context.fill()
    for i in self.all_elements():
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
 
  def all_elements(self):
    yield self.name

  def draw_elements(self):
    yield self.name
     
  def in_area(self, position):
    x, y = position
    return (self.position.x < x < self.position.x + 32 and self.position.y < y < self.position.y + 32) or self.in_chield_area(position)
  
  def move_to(self, position):
    self.move(position - self.position - vector(x = 16))
  
  def move(self, position):
    self.position += position
    self.area.move(position)
    for i in self.all_elements():
      i.move(position)
      
  def button_release(self, position):
    self.parent.area_change_notify()

  def targeted_notify(self, arrow):
    if self.target_arrow:
      self.target_arrow.parent.delete_arrow()
    self.target_arrow = arrow

  def untargeted_notify(self):
    self.target_arrow = None

  def area_change_notify(self):
    self.parent.area_change_notify()

  def key_press(self, keyval):
    if keyval == gtk.keysyms.Delete:
      if self.target_arrow:
        self.target_arrow.parent.delete_arrow()
      self.parent.delete(self)
      redraw()
    else:
      self.parent.key_press(keyval)
        
class attribute(parameter):
  def __init__(self, parent, position):
    super(attribute, self).__init__(parent, position)
    self.name = text(self, self.position - vector(6, 0))
    self.area = area(self.position, self.position + vector(32, 32))
    self.color = (.0, .6, .0)
    self.arrow = None

  def area_change_notify(self):
    self.name.move(vector(6 + self.position.x - self.name.area.right, 0))
    self.parent.area_change_notify()
      
  def key_press(self, keyval):
    global selection_on_mouse
    if keyval == gtk.keysyms.less:
      if self.arrow:
        if self.arrow.target:
          self.arrow.target.untargeted_notify()
        self.arrow = None
      self.arrow = arrow(self, mouse_position)
      select(self.arrow)
      selection_on_mouse = True
      redraw()
    elif keyval == gtk.keysyms.Delete:
      self.parent.delete(self)
      redraw()
    else:
      self.parent.key_press(keyval)

  def all_elements(self):
    if self.arrow:
      yield self.arrow
    yield self.name

  def delete_arrow(self):
    self.arrow = None

class parameter_as_attribute(attribute):
  def __init__(self, parent, position):
    super(parameter_as_attribute, self).__init__(parent, position)
    self.color = (1.0, 0.8, .0)


class arrow(element):
  def __init__(self, parent, target_position):
    self.parent = parent
    self.target_position = target_position
    self.target = None

  def draw(self, context):
    origin = self.parent.area.topleft + vector(16, 16)
    context.move_to(origin.x, origin.y)
    if self.target:
      context.line_to(self.target.area.left + 16, self.target.area.top + 16)
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
    if selection == self:
      self.target_position = position
      redraw()

  def button_release(self, keyval):
    pass
  
  def unselect_notify(self):
    for i in self.parent.parent.i_parameters():
      if i.in_area(self.target_position):
        self.target = i
	self.target.targeted_notify(self)
	return
    self.target = self.parent.parent.add_post_call(self, self.target_position)
    

class call(container):
  def __init__(self, parent, position):
    self.parent = parent
    self.area = area(position, position + vector(32, 32))
    self.name = text(self, self.area.topleft)
    self.attributes = []
    self.parameters = []
    self.color = (0.9, 0.6, 0.1)
    self.arrow = None

  def delete(self, element):
    if type(element) == attribute:
      self.attributes.remove(element)
    elif type(element) == parameter:
      self.parameters.remove(element)
    if selection == element:
      select(self)

  def i_parameters(self):
    return self.parent.i_parameters()

  def i_arrows(self):
    if self.arrow:
      yield self.arrow
    for i in self.attributes:
      if i.arrow:
        yield i.arrow

  def draw_elements(self):
    yield self.name
    for i in self.attributes:
      yield i
    for i in self.parameters:
      yield i

  def all_elements(self):
    if self.arrow:
      yield self.arrow
    for i in self.draw_elements():
      yield i
  
  def add_post_call(self, arrow, position):
    return self.parent.add_post_call(arrow, position)
  
  def in_area(self, position):
    return position in self.area or self.in_chield_area(position)

  def move(self, position):
    self.area.move(position)
    for i in self.all_elements():
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
    global selection_on_mouse
    if keyval in (gtk.keysyms.Control_L, gtk.keysyms.Control_R):
      self.parameters.append(parameter(self, vector(self.area.left - 16, mouse_position.y)))
      self.area_change_notify()
      select(self.parameters[-1])
    elif keyval in (gtk.keysyms.Alt_L, gtk.keysyms.Alt_R):
      self.attributes.append(attribute(self, vector(self.area.right - 16, mouse_position.y)))
      self.area_change_notify()
      select(self.attributes[-1])
    elif keyval == gtk.keysyms.less:
      if self.arrow:
        if self.arrow.target:
          self.arrow.target.untargeted_notify()
        self.arrow = None
      self.arrow = arrow(self, mouse_position)
      select(self.arrow)
      selection_on_mouse = True
    elif keyval == gtk.keysyms.Delete:
      self.parent.delete(self)
      redraw()
    else:
      self.parent.key_press(keyval)
      return
    redraw()

  def delete_arrow(self):
    self.arrow = None

class string(call):
  def __init__(self, parent, position):
    super(string, self).__init__(parent, position)
    self.color = (.8, .3, .2)

class integer(call):
  def __init__(self, parent, position):
    super(integer, self).__init__(parent, position)
    self.color = (.8, .4, .8)

class array(call):
  def __init__(self, parent, position):
    super(array, self).__init__(parent, position)
    self.color = (.2, .1, 1.0)

class case(call):
  def __init__(self, parent, position):
    super(case, self).__init__(parent, position)
    self.color = (.9, 0.5, 0.7)

class post_call(call):
  def __init__(self, parent, position, target_arrow=None):
    super(post_call, self).__init__(parent, position)
    self.color = (.8, 1.0, .4)
    self.target_arrow = target_arrow

  def key_press(self, keyval):
    if keyval == gtk.keysyms.Delete:
      if self.target_arrow:
        self.target_arrow.parent.delete_arrow()
      self.parent.delete(self)
      redraw()
    else:
      super(post_call, self).key_press(keyval)
  def targeted_notify(self, arrow):
    if self.target_arrow:
      self.target_arrow.parent.delete_arrow()
    self.target_arrow = arrow

  def untargeted_notify(self):
    self.target_arrow = None


class function(container):
  def __init__(self, parent, position):
    self.parent = parent
    self.area = area(position, position + vector(32, 32))
    self.name = text(self, self.area.topleft)
    self.attributes = []
    self.parameters = []
    self.elements = []

  def delete(self, element):
    if type(element) == attribute:
      self.attributes.remove(element)
    elif type(element) == parameter:
      self.parameters.remove(element)
    else:
      self.elements.remove(element)
    if selection == element:
      select(self)

  def all_elements(self):
    yield self.name
    for i in self.attributes:
      yield i
    for i in self.parameters:
      yield i
    for i in self.elements:
      yield i

  def i_arrows(self):
    for i in self.attributes:
      if i.arrow:
        yield i.arrow
    for i in self.elements:
      for j in i.i_arrows():
        yield j

  def i_parameters(self):
    for i in self.parameters:
      yield i
    for i in self.elements:
      for j in i.parameters:
        yield j
    for i in self.elements:
      if type(i) == post_call:
        yield i

  def key_press(self, keyval):
    global selection_on_mouse
    if keyval in (gtk.keysyms.Control_L, gtk.keysyms.Control_R):
      self.attributes.append(attribute(self, vector(self.area.left - 16, mouse_position.y)))
      self.area_change_notify()
      select(self.attributes[-1])
    elif keyval == gtk.keysyms.p:
      self.attributes.append(parameter_as_attribute(self, vector(self.area.left - 16, mouse_position.y)))
      self.area_change_notify()
      select(self.attributes[-1])
    elif keyval in (gtk.keysyms.Alt_L, gtk.keysyms.Alt_R):
      self.parameters.append(parameter(self, vector(self.area.right - 16, mouse_position.y)))
      self.area_change_notify()
      select(self.parameters[-1])
    elif keyval == gtk.keysyms.exclam:
      self.elements.append(call(self, mouse_position - vector(6,6)))
      select(self.elements[-1])
      selection_on_mouse = True
      self.area_change_notify()
    elif keyval == gtk.keysyms.quotedbl:
      self.elements.append(string(self, mouse_position - vector(6,6)))
      select(self.elements[-1])
      selection_on_mouse = True
      self.area_change_notify()
    elif keyval == gtk.keysyms.i:
      self.elements.append(integer(self, mouse_position - vector(6,6)))
      select(self.elements[-1])
      selection_on_mouse = True
      self.area_change_notify()
    elif keyval == gtk.keysyms.a:
      self.elements.append(array(self, mouse_position - vector(6,6)))
      select(self.elements[-1])
      selection_on_mouse = True
      self.area_change_notify()
    elif keyval == gtk.keysyms.c:
      self.elements.append(case(self, mouse_position - vector(6,6)))
      select(self.elements[-1])
      selection_on_mouse = True
      self.area_change_notify()
    elif keyval == gtk.keysyms.Delete:
      self.parent.delete(self)
    else:
      self.parent.key_press(keyval)
      return
    redraw()

  def add_post_call(self, arrow, position):
    self.elements.append(post_call(self, position, arrow))
    self.area_change_notify()
    redraw()
    return self.elements[-1]
    

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

    if selection == self:
      self.draw_shadow(context)
    self.draw_box(context, self.area.left, self.area.top)
    context.set_source_rgb(188.0/255, 239.0/255, 245.0/255)
    context.fill()
    
    for i in self.i_arrows():
      i.draw(context)
  
    for i in self.all_elements():
      i.draw(context)
  

  def in_area(self, position):
    x, y = position
    return position in self.area or self.in_chield_area(position)

class includes(container):
  def __init__(self, parent, position):
    self.parent = parent
    self.area = area(position, position +vector(32, 32))
    self.color = (.1, .4, .0)
    self.elements = [text(self, self.area.topleft)]

  def draw_elements(self):
    for i in self.elements:
      yield i

  def in_area(self, position):
    return position in self.area

  def area_change_notify(self):
    width = 32
    for i in self.elements:
      width = max(width, i.area.width)

    self.area.size = vector(width, len(self.elements) * 32)

  def button_press(self, position):
    chield = self.in_chield_area(position)
    if chield:
      chield.button_press(position)
    else:
      select(self)
      i = 0
      while i < len(self.elements):
        if self.elements[i].text == "":
          del self.elements[i]
        else:
          self.elements[i].move_to(self.area.topleft + vector(0, + i * 32))
          i += 1
      self.elements.append(text(self, self.area.topleft + vector(0, len(self.elements) * 32)))
      self.area_change_notify()
    redraw()

  def key_press(self, keyval):
    if keyval == gtk.keysyms.Delete:
      self.parent.delete(self)
      redraw()
    else:
      self.parent.key_press(keyval)

class root(foobar):
  def __init__(self):
    #self.parent = None

    self.elements = []
    self.area = area(vector(), vector(800, 600))

  def delete(self, element):
    self.elements.remove(element)


  def draw(self, context):
    for i in self.elements:
      i.draw(context)

  def key_press(self, keyval):
    global selection_on_mouse
    if keyval == gtk.keysyms.Escape:
      quit()
    elif keyval == gtk.keysyms.space:
      self.elements.append(function(self, mouse_position - vector(6,6)))
      select(self.elements[-1])
      selection_on_mouse = True
      redraw()
    elif keyval == gtk.keysyms.i:
      self.elements.append(includes(self, mouse_position - vector(6,6)))
      select(self.elements[-1])
      selection_on_mouse = True
      redraw()

  def move(self, position):
    pass
  
def main():
  global drawing_area, window, root_widget, selection, mouse_position, selection_on_mouse
  drawing_area = gtk.DrawingArea()

  drawing_area.connect("expose_event", expose)
  drawing_area.connect("button_press_event", button_press)
  drawing_area.connect("button_release_event", button_release)
  drawing_area.connect("motion_notify_event", motion_notify)
  drawing_area.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK)

  window = gtk.Window()
  drawing_area.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(65535, 65535, 65535))
  window.add(drawing_area)
  window.connect("destroy", gtk.main_quit)
  window.connect("key_press_event", key_press)
  window.connect("key_release_event", key_release)

  try:
   f = open(sys.argv[1], "r")
   root_widget = pickle.load(f)
   f.close()
   window.set_default_size(root_widget.area.width, root_widget.area.height)
  except IOError:
   root_widget = root()
   window.set_default_size(800, 600)
  selection = root_widget
  mouse_position = vector()
  selection_on_mouse = False


  window.show_all()
  gtk.main()
 
def select(element):
  global selection
  if not selection == element:
    selection.unselect_notify()
    selection = element

def quit():
  gtk.main_quit()

def motion_notify(widget, event):
  global mouse_position
  root_widget.motion_notify(vector(event.x, event.y))
  mouse_position = vector(event.x, event.y)

def button_press(widget, event):
  global selection_on_mouse
  selection_on_mouse = True
  root_widget.button_press(vector(event.x, event.y))
  
def button_release(widget, event):
  global selection_on_mouse
  selection_on_mouse = False
  root_widget.button_release(vector(event.x, event.y))
  redraw()

def key_press(widget, event):
  for i in gtk.keysyms.__dict__.iteritems():
    if i[1] == event.keyval:
      print i[0]
  if event.keyval == gtk.keysyms.F1:
    f = open(sys.argv[1], "w")
    pickle.dump(root_widget, f)
    f.close()
  else:
    selection.key_press(event.keyval)
  
def key_release(widget, event):
  pass

def expose(widget, event):
    context = widget.window.cairo_create()
    context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
    context.clip()
    context.set_line_width(1)
    drawing_area.width = event.area.width
    drawing_area.height = event.area.height
    root_widget.area.size = vector(event.area.width, event.area.height)
    draw(context)
    return False
  
def redraw():
    if window:
      alloc = drawing_area.get_allocation()
      drawing_area.queue_draw_area(alloc.x, alloc.y, alloc.width, alloc.height)

def draw(context):
  root_widget.draw(context)


if __name__ == "__main__":
  main()
