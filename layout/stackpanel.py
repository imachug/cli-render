from rect import Rect
from switch import Switch
from exceptions import NoStretchError

class StackPanel(Rect):
	container = True
	text_container = False

	def __init__(self, width=None, height=None, bg=None, orientation="horizontal", children=[]):
		super(StackPanel, self).__init__(width=width, height=height, bg=bg)

		self.vertical = orientation.lower() == "vertical"
		self.children = children

	def render(self, layout, dry_run=False):
		# Guess container size
		if self.vertical:
			stretch = self.width
		else:
			stretch = self.height

		if self.width is None or self.height is None:
			# Let guessContainerSize() find out 'stretch' if it is not given
			width, height, stretch = self.guessContainerSize(layout, stretch=stretch)
			if self.width is not None:
				width = self.width
			if self.height is not None:
				height = self.height
		else:
			# If the size is given, don't do unnecessary actions
			width, height = self.width, self.height

		x1, y1, x2, y2 = super(StackPanel, self).render(layout, dry_run=dry_run, width=width, height=height)
		self.renderChildren(layout, x1, y1, x2, y2, dry_run=dry_run, stretch=stretch)

		return x1, y1, x2, y2

	def guessContainerSize(self, layout, stretch=None):
		x1, y1, x2, y2 = super(StackPanel, self).render(layout, dry_run=True, width=self.width or 0, height=self.height or 0)

		return self.renderChildren(layout, x1, y1, x2, y2, dry_run=True, stretch=stretch)

	def renderChildren(self, layout, x1, y1, x2, y2, dry_run=False, stretch=None):
		cur_x, cur_y = x1, y1
		max_width, max_height = 0, 0

		rows_columns = []

		row_column_has_stretch_problems = False
		rows_columns_no_stretch = []

		for child in self.children:
			if isinstance(child, Switch):
				# <Switch /> can be used to switch direction
				if self.vertical:
					if not row_column_has_stretch_problems:
						rows_columns_no_stretch.append(cur_y - y1)

					cur_x += max_width
					cur_y = y1

					rows_columns.append(max_width)
					max_width = 0
				else:
					if not row_column_has_stretch_problems:
						rows_columns_no_stretch.append(cur_x - x1)

					cur_x = x1
					cur_y += max_height

					rows_columns.append(max_height)
					max_height = 0

				row_column_has_stretch_problems = False
				continue

			child.render_offset = (cur_x, cur_y)

			child.render_boundary_left_top = self.render_boundary_left_top
			child.render_boundary_right_bottom = self.render_boundary_right_bottom

			if self.width is not None:
				child.render_boundary_left_top[0] = x1
				child.render_boundary_right_bottom[0] = x2
			if self.height is not None:
				child.render_boundary_left_top[1] = y1
				child.render_boundary_right_bottom[1] = y2

			child.parent = self
			child.render_stretch = stretch

			try:
				child_x1, child_y1, child_x2, child_y2 = child.render(layout, dry_run=dry_run)
			except NoStretchError:
				row_column_has_stretch_problems = True
				continue

			max_width = max(max_width, child_x2 - child_x1)
			max_height = max(max_height, child_y2 - child_y1)

			if self.vertical:
				cur_y = child_y2
			else:
				cur_x = child_x2

		if len(rows_columns_no_stretch) < len(rows_columns):
			# Some rows/columns used 'stretch' variable, which was not calculated yet
			if self.vertical:
				stretch = sum(rows_columns_no_stretch) + cur_y - y1
			else:
				stretch = sum(rows_columns_no_stretch) + cur_x - x1

			return self.renderChildren(layout, x1, y1, x2, y2, dry_run=dry_run, stretch=stretch)

		if self.vertical:
			return sum(rows_columns) + max_width, cur_y - y1, stretch
		else:
			return cur_x - x1, sum(rows_columns) + max_height, stretch