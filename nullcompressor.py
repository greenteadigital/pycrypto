
class NullCompressor(object):

	def __init__(self):
		self.__name__ = 'none'

	def compress(self, _input):
		return _input