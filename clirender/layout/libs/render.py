from library import Library
import all

def getLibInfo(lib):
	if isinstance(lib, type) and issubclass(lib, Library):
		return lib

	if not hasattr(all, lib):
		raise AttributeError("No %s lib" % lib)
	return getattr(all, lib)

def getDependencies(libs):
	res = []
	for lib in libs:
		dependencies = getattr(getLibInfo(lib), "dependencies", [])
		res += getDependencies(dependencies)
		res.append(lib)
	return res

def getAdditionalNodes(libs):
	from ..nodes import Node, Generator

	nodes = {}
	for lib in getDependencies(libs):
		info = getLibInfo(lib)

		for obj in dir(info):
			try:
				if issubclass(getattr(info, obj), (Node, Generator)):
					nodes[obj] = getattr(info, obj)
			except TypeError:
				pass

	return nodes

def getAdditionalSlots(libs):
	slots = {}
	for lib in getDependencies(libs):
		info = getLibInfo(lib)

		for obj in dir(info):
			try:
				if hasattr(getattr(info, obj), "slot"):
					slots[getattr(info, obj).slot] = getattr(info, obj).__func__
			except TypeError, e:
				pass

	return slots

def register(name, lib):
	setattr(all, name, lib)

def render(layout, libs):
	layout.screen.changeCursor(False)
	import atexit
	atexit.register(lambda: layout.screen.changeCursor(True))

	libs = getDependencies(libs)

	lib_instances = {}
	for lib in libs:
		lib_instances[lib] = getLibInfo(lib)(layout)

	layout.libs = lib_instances
	layout.render(force=True)

	if any(hasattr(lib, "loop") for lib in lib_instances.values()):
		while True:
			for lib in lib_instances.values():
				if hasattr(lib, "beforeLoop"):
					lib.beforeLoop(lib_instances)
			for lib in lib_instances.values():
				if hasattr(lib, "loop"):
					lib.loop(lib_instances)

			layout.render(clear=False)