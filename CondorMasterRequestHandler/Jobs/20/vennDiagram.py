from PIL import Image, ImageDraw, ImageFont
import StringIO, base64

class VennDiagram:
	def __init__(self, circles=3):
		if circles != 3:
			raise ValueError, "Currently only Venn Diagrams with 3 surfaces can be constructed."
		self.circles = circles
		self.loadedData = {}
	
	def loadData(self, data, location, column=1):
		# location should be the position of the data in relation to the other items
		# ie (3) would cover the area of ONLY item 3, whereas (1,2) would cover the
		# overlap between 1 and 2
		newData = {}
		if isinstance(data, file):
			newData['type'] = data.name.split(".")[-1]
			newData['data'] = data.read()
		if isinstance(data, str):
			if len(data) < 20 and "." in data:
				newData['type'] = data.split(".")[-1]
				newData['data'] = open(data).read()
			else:
				newData['data'] = data
				newData['type'] = "String"
		
		if newData['type'] == "csv":
			newData['data'] = self.parseCSV(newData['data'], column=column)
		
		self.loadedData[location] = newData
		
	def parseCSV(self, data, column=1, all=False):
		delimiter = max([(char, data.count(char)) for char in [",",";","|"]], key=lambda k: k[1])[0]
		newData = []
		for line in data.split("\n"):
			try:
				newData.append( line.split(delimiter)[column].strip('"') )
			except:
				pass
		return newData
		
	def drawCircle(self, fill_rgb, xy , canvas ):
		color_layer = Image.new('RGBA', canvas.size, fill_rgb)
		alpha_mask = Image.new('L', canvas.size, 0)
		alpha_mask_draw = ImageDraw.Draw(alpha_mask)
		
		x1 = canvas.size[0]*xy[0]
		y1 = canvas.size[1]*xy[1]
		x2 = x1+canvas.size[0]*0.6
		y2 = y1+canvas.size[1]*0.6
		
		bbox = (x1,y1,x2,y2)
		alpha_mask_draw.ellipse(bbox, fill=140)
		
		return Image.composite(color_layer, canvas, alpha_mask), (x1+((x2-x1)/2), y1+((y2-y1)/2))
		
	def calculateProportions(self):
		lengths = []
		for key, data in self.loadedData.items():
			lengths.append( (key, len(data['data']) ) )
			
		lengths.sort(key=lambda k: k[1])
		median = lengths[int( len(lengths)/2 )][1]
		
		proportions = []
		for length in lengths:
			proportions.append( ( length[0], float(length[1])/median ) )
		
		print dict(proportions)
		
	def drawDiagram(self, width, height, aa=1):
		fontSize = 30 *aa
		self.font = ImageFont.truetype(
			'C:\\Windows\\Fonts\\Arial.ttf', fontSize
		)
		self.font2 = ImageFont.truetype(
			'C:\\Windows\\Fonts\\Arial.ttf', int(fontSize*0.5)
		)
	
		canvas = Image.new("RGB", (width*aa, height*aa), "white")
		
		colors = ("red","blue","yellow")
		positions = ((0,0), (0.4,0),(0.2,0.4))	
		centers = []
		
		
		for circle in range(self.circles):			
			result = self.drawCircle(colors[circle],
									 positions[circle],
									 canvas)
			canvas = result[0]
			center = result[1]
			centers.append(center)
			
			print center
			canvDraw = ImageDraw.Draw(canvas)
			text = "Patient %s:" % (circle+1)
			text2 = str( len(self.loadedData[(circle+1,)]['data']))
			size = canvDraw.textsize(text, font=self.font2)
			size2 = canvDraw.textsize(text2, font=self.font)
			
			
			canvDraw.text(	(center[0]-size[0]/2, center[1]-size[1]/2 - fontSize/2 ),
							text,
							font=self.font2,
							fill="black")
			canvDraw.text(	(center[0]-size2[0]/2, center[1]-size2[1]/2 + fontSize/2),
							text2,
							font=self.font,
							fill="black")
							

		trueCenter = ( canvas.size[0]/2, canvas.size[1]/2*0.9)
		overlaps = {
			(1,2,3) : trueCenter,
			(1,2) : ( centers[0][0] + abs(centers[1][0] - centers[0][0])/2, # Difference on the X-axis, divided by 2, added to the center of the lowest
					  centers[0][1] + abs(centers[1][1] - centers[0][1])/2), # Difference on the X-axis, divided by 2, added to the center of the lowest 
			(1,3) : ( centers[0][0] + abs(centers[2][0] - centers[0][0])/2,
					  centers[0][0] + abs(centers[2][1] - centers[0][1])/2),
			(2,3) : ( centers[2][0] + abs(centers[1][0] - centers[2][0])/2,
					  centers[1][1] + abs(centers[1][1] - centers[2][1])/2),
		}
		
		#print overlaps
		
		for key, ocenter in overlaps.items():
			print key, ocenter, len( self.loadedData[key]['data'] )
			center = ocenter
			text = str(len(self.loadedData[( key )]['data']))
			size = canvDraw.textsize(text, font=self.font)
			canvDraw.text(	(center[0]-size[0]/2, center[1]-size[1]/2),
							text,
							font=self.font,
							fill="black")
		
		if aa > 1:
			canvas.resize((width, height))
		return canvas

if __name__ == "__main__":
	VD = VennDiagram(3)
	VD.loadData(open("Unique1.csv"),(1,) )
	VD.loadData(open("Unique2.csv"),(2,) )
	VD.loadData(open("Unique3.csv"),(3,) )
	VD.loadData(open("Consensus.csv"),(1,2,3) )
	VD.loadData(open("Overlap12.csv"),(1,2) )
	VD.loadData(open("Overlap13.csv"),(1,3) )
	VD.loadData(open("Overlap23.csv"),(2,3) )	
	
	VD.calculateProportions()
	canvas = VD.drawDiagram(768,768, aa=2)
	
	f = StringIO.StringIO()
	canvas.save(f, format="PNG")
	print "\n\ndata:" + base64.b64encode(f.getvalue())