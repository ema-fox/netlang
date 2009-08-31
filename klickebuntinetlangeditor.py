#!/usr/bin/python

debug = False

import gtk, gtk.keysyms, math

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
    self.position += position
  
  def key_press(self, keyval):
    self.parent.key_press(keyval)

  def draw_shadow(self, context):
    pass
  
class container(area):
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
    self.draw_box(context, self.position.x + 3, self.position.y +3)
    context.set_source_rgba(0,0,0, 0.3)
    context.fill()
    for i in self.i_elements():
      i.draw_shadow(context)


  def move(self, position):
    self.position += position
    for i in self.i_elements():
      i.move(position)
        
  def button_press(self, position):
    chield = self.in_chield_area(position)
    if chield:
      chield.button_press(position)
    else:
      self.drawing_area.select(self)
    self.drawing_area.redraw()


class text(area):
  def __init__(self, drawing_area, parent, position):
    self.super().__init__(drawing_area, parent)
    self.text = u""
    self.position = position

  def draw(self, context):
    x = self.position.x
    y = self.position.y
    if debug:
      context.rectangle(x, y, 2, 2)
      context.set_source_rgb(1.0, .0, .0)
      context.fill()
    if debug:
      left, top, right, bottom = self.area()
      context.rectangle(left, top, 2, 2)
      context.set_source_rgb(1.0, 1.0, .0)
      context.fill()
      context.rectangle(right, bottom, 2, 2)
      context.set_source_rgb(.0, 1.0, .0)
      context.fill()

    textlayout = context.create_layout()
    textlayout.set_font_description(self.drawing_area.get_style().font_desc)
    textlayout.set_text(self.text)
    s = textlayout.get_pixel_size()
    if self.drawing_area.selection == self:
      context.rectangle(x, y, s[0] + 12, s[1] + 12)
      context.set_source_rgba(0,0,0,0.1)
      context.fill()

    context.move_to(x + 6, 6 + y)
    context.set_source_rgb(.0, .0, .0)
    context.show_layout(textlayout)
  def area(self):
    context = self.drawing_area.window.cairo_create()
    textlayout = context.create_layout()
    textlayout.set_font_description(self.drawing_area.get_style().font_desc)
    textlayout.set_text(self.text)
    s = vector(textlayout.get_pixel_size())
    left = self.position.x
    right = self.position.x + s.x + 12
    return vector(left, self.position.y), vector(right, self.position.y + s.y + 12)
    

  def in_area(self, position):
    (left, top), (right, bottom) = self.area()
    return left < position.x < right and top < position.y < bottom

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
    self.parent.area_change_notify(self.area())
    self.drawing_area.redraw()

  def move_to(self, position):
    self.position = position
    

class attribute(container):
  def __init__(self, drawing_area, parent, position, direction):
    super(attribute, self).__init__(drawing_area, parent)
    self.position = position
    self.direction = direction
    self.elements = [text(drawing_area, self, self.position - vector(x = 6))]

  def area_change_notify(self, area):
    if self.direction == "left":
      self.elements[0].move(vector(6 + self.position.x - area[1].x, 0))
      
  def set_direction(self, direction):
    self.direction = direction
    if self.direction == "left":
      self.elements[0].move(vector(6 + self.position.x - self.elements[0].area()[1].x, 0))
    else:
      self.elements[0].move_to(self.position + vector(26, 0))
      
  def draw(self, context):
    x, y = self.position
    if debug:
      context.rectangle(x, y, 2, 2)
      context.set_source_rgb(1.0, .0, .0)
      context.fill()

    if self.drawing_area.selection == self:
      self.draw_shadow(context)

    for i in self.elements:
      i.draw(context)

    self.draw_box(context, x, y)
    context.set_source_rgb(0.1, 0.7, 0.1)
    context.fill()

  def draw_box(self, context, x, y, r=10):
    x += 6
    y += 6
    context.move_to(x, y+r)
    context.curve_to(x,y, x+r,y, x+r,y)
    context.curve_to(x+r*2,y, x+r*2,y+r, x+r*2,y+r)
    context.curve_to(x+r*2,y+r*2, x+r,y+r*2, x+r,y+r*2)
    context.curve_to(x,y+r*2, x,y+r, x,y+r)
    context.close_path()
 
  def in_area(self, position):
    x, y = position
    return (self.position.x < x < self.position.x + 32 and self.position.y < y < self.position.y + 32) or self.in_chield_area(position)
  
  def button_release(self, position):
    if self.drawing_area.selection == self:
      self.parent.change_position(self)

  def move_to(self, position):
    self.move(position - self.position - vector(x = 16))
  
  def key_press(self, keyval):
    if keyval == gtk.keysyms.less:
      try:
        del self.elements[1]
      except IndexError:
        pass
      self.elements.append(arrow(self.drawing_area, self, self.drawing_area.mouse_position))
      self.drawing_area.select(self.elements[1])
      self.drawing_area.selection_on_mouse = True
      self.drawing_area.redraw()
    else:
      self.parent.key_press(keyval)
  def delete(self, element):
    self.elements.remove(element)

class arrow(area):
  def __init__(self, drawing_area, parent, tartget_position):
    self.super().__init__(drawing_area, parent)
    self.tartget_position = tartget_position
    self.tartget = None

  def draw(self, context):
    origin = self.parent.position + vector(16, 16)
    context.move_to(origin.x, origin.y)
    if self.tartget:
      context.line_to(self.tartget.position.x + 16, self.tartget.position.y + 16)
    else:
      context.line_to(self.tartget_position.x, self.tartget_position.y)
    context.close_path()
    context.set_source_rgb(.0, .0, .0)
    context.stroke()
   
  def in_area(self, position):
    return False
  
  def move(self, position):
    pass

  def motion_notify(self, position):
    if self.drawing_area.selection == self:
      self.tartget_position = position
      self.drawing_area.redraw()
  
  def unselect_notify(self):
    element = self.parent.parent.in_chield_area(self.tartget_position)
    if type(element) == attribute:
      self.tartget = element
    else:
      self.parent.delete(self)


class function(container):
  def __init__(self, drawing_area, parent, position):
    self.super().__init__(drawing_area, parent)
    self.position = position
    self.size = vector(32, 32)
    self.elements_left = [text(self.drawing_area, self, self.position)]
    self.elements_right = []

  def i_elements(self):
    for i in self.elements_left:
      yield i
    for i in self.elements_right:
      yield i
  
  def key_press(self, keyval):
    if keyval in (gtk.keysyms.Control_L, gtk.keysyms.Control_R):
      self.elements_left.append(attribute(self.drawing_area, self, self.position + vector(-16, len(self.elements_left) * 32), "left"))
      self.new_size()
      self.drawing_area.select(self.elements_left[-1])
    else:
      self.parent.key_press(keyval)
      return
    self.drawing_area.redraw()

  def new_size(self):
    self.size = vector(self.size.x, max(len(self.elements_left), len(self.elements_right)) *32)

  def area_change_notify(self, area):
    self.size = vector(max(10 + area[1].x - area[0].x, 32), self.size.y)
    self.fix_position()

  def draw(self, context):
    if debug:
      context.rectangle(self.position.x, self.position.y, 2, 2)
      context.set_source_rgb(1.0, .0, .0)
      context.fill()

    if self.drawing_area.selection == self:
      self.draw_shadow(context)
    self.draw_box(context, self.position.x, self.position.y)
    context.set_source_rgb(188.0/255, 239.0/255, 245.0/255)
    context.fill()
    
    if (self.drawing_area.selection in self.i_elements()) and self.drawing_area.selection_on_mouse:
      nearest = self.nearest(self.drawing_area.selection)
      for i in xrange(len(self.elements_left) + 1):
        context.rectangle(self.position.x, self.position.y + i * 32, 12, 2)
	if i == nearest.y and nearest.x == 0:
          context.set_source_rgb(1.0, 1.0, .0)
        else:
          context.set_source_rgb(1.0, .0, .0)
        context.fill()
      for i in xrange(len(self.elements_right) + 1):
        context.rectangle(self.position.x + self.size.x - 12, self.position.y + i * 32, 12, 2)
	if i == nearest.y and nearest.x == 1:
          context.set_source_rgb(1.0, 1.0, .0)
        else:
          context.set_source_rgb(1.0, .0, .0)
        context.fill()

    for i in self.i_elements():
      i.draw(context)
  
  def nearest(self, element):
    x, y = element.position
    nearest = vector()
    for i in xrange(max(len(self.elements_left), len(self.elements_right))):
      if abs(y - (self.position.y + 32 * nearest.y)) > abs(y - (self.position.y + 32 * (i+1))):
        nearest = vector(nearest.x, i+1)
    
    if abs(x - self.position.x) < abs(x - (self.position.x + self.size.x)):
      nearest = vector(0, min(nearest.y, len(self.elements_left)))
    else:
      nearest = vector(1, min(nearest.y, len(self.elements_right)))
    return nearest
 
  def change_position(self, element):
    try:
      self.elements_left.remove(element)
    except ValueError:
      self.elements_right.remove(element)
    nearest = self.nearest(element)
    if nearest.x == 0:
      self.elements_left.insert(nearest.y, element)
      element.set_direction("left")
    else:
      self.elements_right.insert(nearest.y, element)
      element.set_direction("right")
    self.fix_position()

  def fix_position(self):
    for i in xrange(len(self.elements_left)):
      self.elements_left[i].move_to(self.position + vector(y = 32 * i))
    for i in xrange(len(self.elements_right)):
      self.elements_right[i].move_to(self.position + vector(self.size.x, 32 * i))
    self.new_size()
  
  def draw_box(self, context, x, y, r=16):
    w, h = self.size
    context.move_to(x, y+r)
    context.curve_to(x,y, x+r,y, x+r,y)
    context.line_to(x+w-r, y)
    context.curve_to(x+w,y, x+w,y+r, x+w,y+r)
    context.line_to(x+w, y+h-r)
    context.curve_to(x+w,y+h, x+w-r,y+h, x+w-r,y+h)
    context.line_to(x+r, y+h)
    context.curve_to(x,y+h, x,y+h-r, x,y+h-r)
    context.close_path()
  def in_area(self, position):
    x, y = position
    return (self.position.x < x < self.position.x + self.size.x and self.position.y < y < self.position.y + self.size.y) or self.in_chield_area(position)


class root(container):
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
    elif keyval in (gtk.keysyms.Alt_L, gtk.keysyms.Alt_R):
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
