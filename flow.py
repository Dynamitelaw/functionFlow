'''
###############################################################
flow.py
by Jose Rubianes

FunctionFlow v1.02
	Contains the code to generate a call graph
	for all the functions in a project directory.

	For usage help: $python flow.py -h

Prerequisites:
	graphviz
		$sudo apt-get install graphviz

###############################################################
'''

import os
import argparse
import random
import textwrap
import sys
import math


#==========================================================================
#		Global Variables
#==========================================================================

verbose = False
lineNumbers = False




#==========================================================================
#		Graph Builder Functions
#==========================================================================

def graphDirectory(directory, fileExtension):
	'''
	Creates subgraphs for all source code files in the specified directory
	Outputs all subgraphs as a list
	'''

	if (verbose):
		print ("Graphing directory")

	parentfileList = os.listdir(os.path.abspath(directory))
	subgraphs = []

	for file in parentfileList:
		if ((file.find(fileExtension)) != -1):
			subgraphs.append(createSubgraph((directory+"/"+file), file.split('.')[0]))

	return subgraphs


def translateSubgraph(subgraph, subgraphNumber, cluster, fillColor, functionDefinitionTome):
	'''
	Translates a given subgraph into the DOT (GraphViz) language.
	Outputs resulting functional blocks as a list of strings
	'''

	if (verbose):
		print (" Translating subgraph " + subgraph.name)

	subLinelist = []	#meant for the first section of .gv file
	tailLinelist = []	#meant for the last seciotn of .gv file

	if (cluster):
		#Groups functions defined in files within explicit groups
		subgraphHeader = "subgraph cluster_" + subgraph.name + " {"
	else:
		subgraphHeader = "subgraph nonCluster_" + str(subgraphNumber) + " {"

	subLinelist.append(subgraphHeader)
	
	if (cluster):
		label = "label=" + '"' + subgraph.name + '";'
		subLinelist.append(label)
		style = 'style="filled";'
		subLinelist.append(style)
		clusterFillColor = 'fillcolor="#f0f0f0";'
		subLinelist.append(clusterFillColor)
		clusterRank = 'clusterrank="local"'
		subLinelist.append(clusterRank)

		#Compress rendering of cluster into smaller dimensions
		subgraph.segregate()
		nodesNOTtoCompress = subgraph.nodesNOTtoCompress
		nodesToCompressIntoBlock = subgraph.nodesToCompress

		numberOfNodesToCompress = len(nodesToCompressIntoBlock)
		cluserHeight = int (math.sqrt(numberOfNodesToCompress))
		if (cluserHeight == 0):
			cluserHeight = 1
		clusterWidth = int (float(numberOfNodesToCompress) / cluserHeight) + 1

		addEdgeBetweenCluster = True
		
		for row in range(0,cluserHeight,1):
			#Constructs new graphviz subgraph for each compressed row
			subLinelist.append("subgraph newRow" + str(row) + "_" + subgraph.name + " {")
			subLinelist.append('rank="same";')
			subLinelist.append(subgraph.name + "_row" + str(row) + ' [fontsize=1.0,style="invis"];')

			for i in range(row*(clusterWidth+1),(row+1)*(clusterWidth+1),1):
				if (i<len(nodesToCompressIntoBlock)):
					node = nodesToCompressIntoBlock[i]

					if (lineNumbers):
						subLinelist.append((node.name + "_L" + str(node.line) + ' [style="filled",fillcolor=' + fillColor + '];'))
					else:
						subLinelist.append((node.name + ' [style="filled",fillcolor=' + fillColor + '];'))

					for functionCall in node.calledFunctions:
						if (len(functionCall) > 0):
							foundInTome = False
							for subgraphTomeEntry in functionDefinitionTome:
								headName = subgraphTomeEntry[0]
								if (headName == subgraph.name):
									pass
								else:
									if (functionCall in subgraphTomeEntry[1]):
										#Called function is defined inside another cluster (file)
										foundInTome = True
										break

							if (foundInTome):  #Edges between clusters are failing in some cases. Disabled until I can figure out why
								if (addEdgeBetweenCluster):
									#Calls between clusters to be grouped into a single edge
									if (lineNumbers):
										edge = functionCall + " -> " + node.name + "_L" + str(node.line) + " [lhead=cluster_" + headName + ",ltail=cluster_" + subgraph.name + "];"
									else:
										edge = functionCall + " -> " + node.name + " [ltail=cluster_" + headName + ",lhead=cluster_" + subgraph.name + "];"
									addEdgeBetweenCluster = False

									tailLinelist.append(edge)
							else:
								if (lineNumbers):
									edge = functionCall + " -> " + node.name + "_L" + str(node.line) + ";"
								else:
									edge = functionCall + " -> " + node.name + ";"
							
								tailLinelist.append(edge)

				else:
					break

			subLinelist.append("}")


		for node in nodesNOTtoCompress:
			if (lineNumbers):
				subLinelist.append((node.name + "_L" + str(node.line) + ' [style="filled",fillcolor=' + fillColor + '];'))
			else:
				subLinelist.append((node.name + ' [style="filled",fillcolor=' + fillColor + '];'))

			for functionCall in node.calledFunctions:
				if (len(functionCall) > 0):
					foundInTome = False
					for subgraphTomeEntry in functionDefinitionTome:
						headName = subgraphTomeEntry[0]
						if (headName == subgraph.name):
							pass
						else:
							if (functionCall in subgraphTomeEntry[1]):
								#Called function is defined inside another cluster (file)
								foundInTome = True
								break

					if (foundInTome):  
						if (addEdgeBetweenCluster):
							#Calls between clusters to be grouped into a single edge
							if (lineNumbers):
								edge = functionCall + " -> " + node.name + "_L" + str(node.line) + " [lhead=cluster_" + headName + ",ltail=cluster_" + subgraph.name + "];"
							else:
								edge = functionCall + " -> " + node.name + " [ltail=cluster_" + headName + ",lhead=cluster_" + subgraph.name + "];"
							addEdgeBetweenCluster = False

							tailLinelist.append(edge)
					else:
						if (lineNumbers):
							edge = functionCall + " -> " + node.name + "_L" + str(node.line) + ";"
						else:
							edge = functionCall + " -> " + node.name + ";"
					
						tailLinelist.append(edge)


		for row in range(0,cluserHeight-1,1):
			edge = subgraph.name + "_row" + str(row) + " -> " + subgraph.name+"_row"+str(row+1) + ' [style="invis"];'
			subLinelist.append(edge)

	else:
		for node in subgraph.includedNodes:
			if (lineNumbers):
				subLinelist.append((node.name + "_L" + str(node.line) + ' [style="filled",fillcolor=' + fillColor + '];'))
			else:
				subLinelist.append((node.name + ' [style="filled",fillcolor=' + fillColor + '];'))

			for functionCall in node.calledFunctions:
				if (len(functionCall) > 0):
					if (lineNumbers):
						edge = functionCall + " -> " + node.name + "_L" + str(node.line) + ";"
					else:
						edge = functionCall + " -> " + node.name + ";"
					tailLinelist.append(edge)

	subLinelist.append('}')

	return subLinelist, tailLinelist


def translateDirectory(directory, fileExtension, outputFileName, cluster, excludeExternalFunctions):
	'''
	Translates an entire directory into a graph in the DOT (GraphViz) language
	Outputs to specified file
	More info on DOT syntax found here:
		https://graphviz.gitlab.io/_pages/doc/info/lang.html
		https://graphs.grevian.org/example
	'''

	if (verbose):
		print ("Translating all " + fileExtension + " files in " + directory + " to DOT")

	outputLinelist = []		#First section of .gv file
	endLinelist = []		#last section of .gv file
	colorKeyList = []		#color key functional block of .gv file
	nodesDefinedInDirectory = []

	outputLinelist.append('digraph {')
	outputLinelist.append('overlap=false;')
	outputLinelist.append('concentrate=true;')
	outputLinelist.append('compound=true;')
	outputLinelist.append('rankdir="BT";')

	colorKeyList.append('subgraph cluster_key{')
	colorKeyList.append('label="Key";')

	subgraphs = graphDirectory(directory, fileExtension)

	functionDefinitionTome = []
	for subgraph in subgraphs:
		functionDefinitionTome.append([subgraph.name, subgraph.functionNamesDefinedInSubgraph])

	for i in range(0, len(subgraphs), 1):
		nodesDefinedInDirectory += subgraphs[i].includedNodes

		#Each file has its own color of nodes to substitute clustering
		fillColor = randomColorGenerator()
		colorKeyEntry = subgraphs[i].name + '_' + fileExtension[1:] + ' [style="filled", shape=rectangle, fillcolor=' + fillColor + '];'
		colorKeyList.append(colorKeyEntry)

		subLinelist, tailLinelist = translateSubgraph(subgraphs[i], i, cluster, fillColor, functionDefinitionTome)
		outputLinelist += subLinelist
		endLinelist += tailLinelist

	if (excludeExternalFunctions):
		#Deletes edges if called functions are not defined within directory
		if (verbose):
			print ("Deleting external function calls")

		functionsDefinedInDirectory = []

		for node in nodesDefinedInDirectory:
			functionsDefinedInDirectory.append(node.name)

		for i in range(len(endLinelist)-1,-1, -1):
			calledFunction = endLinelist[i].replace(" ","").split("->")[0]
			if (calledFunction in functionsDefinedInDirectory):
				pass
			else:
				del endLinelist[i]

	colorKeyList.append("}")
	outputLinelist += colorKeyList
	outputLinelist += endLinelist
	outputLinelist.append('}')

	outputFile = open(os.path.abspath(outputFileName), 'w')
	for line in outputLinelist:
		outputFile.write(line + "\n")
	
	outputFile.close()


def renderGraph(inputFileName, outputFileName, outputFormat = "png", gFilter="dot", deleteInput = True):
	'''
	Uses GraphViz to render the translated DOT code
	'''

	if (verbose):
		print("Rendering graph")

	command = gFilter + " -T" + outputFormat + " " + inputFileName + " -o" + outputFileName

	if (verbose):
		print("SystemCMD: " + command)

	os.system(command)
	
	if deleteInput:
		os.remove(inputFileName)


def randomColorGenerator():
	'''
	Generates a random RGB color code
	Output is a hex string
	'''

	R = random.randint(144,257)
	G = random.randint(144,257)
	B = random.randint(144,257)

	Rhex = hex(R)[-2:]
	Ghex = hex(G)[-2:]
	Bhex = hex(B)[-2:]

	colorCode = '"#' + Rhex + Ghex + Bhex + '"'
	return colorCode


def sanitizeName(nameIn):
	'''
	Replace characters in function names for DOT error avoidance
	'''
	nameOut = nameIn.replace('::', '_')
	nameOut = nameOut.replace('~', "")
	nameOut = nameOut.replace('%', '_')
	nameOut = nameOut.replace('.', '_')
	nameOut = nameOut.replace('?', '_')
	nameOut = nameOut.replace('|', '_')
	nameOut = nameOut.replace('!', '_')
	nameOut = nameOut.replace(';', '')
	nameOut = nameOut.replace(':', '')

	return nameOut


#==========================================================================
#		subGraph Classes and Definitions 
#==========================================================================

class subGraph:
	def __init__ (self, subGraphName, includedNodes):
		self.name = subGraphName
		self.includedNodes = includedNodes

		self.functionNamesDefinedInSubgraph = []
		for node in self.includedNodes:
			self.functionNamesDefinedInSubgraph.append(node.name)

	def segregate(self):
		'''
		Splits includedNodes into a compressible cluster and a non-compressible cluster
		'''
		functionsCalledInSubgraph = []
		for node in self.includedNodes:
			functionsCalledInSubgraph += node.calledFunctions

		functionsCalledInSubgraph = list( set(functionsCalledInSubgraph) )

		self.nodesToCompress = []
		self.nodesNOTtoCompress = []

		for node in self.includedNodes:
			compressible = True
			if (node.name in functionsCalledInSubgraph):
				#This node is called by another function in this subgraph
				compressible = False
			elif (len( list( set(node.calledFunctions) & set(self.functionNamesDefinedInSubgraph) ) ) > 0):
				#This node calls other functions defined within this subgraph
				compressible = False

			if (compressible):
				self.nodesToCompress.append(node)
			else:
				self.nodesNOTtoCompress.append(node)



class Node:
	def __init__(self, functionName, parentName, definitionLineNumber, className):
		self.name = functionName
		self.parentName = parentName
		self.line = definitionLineNumber
		self.className = className
		self.arguments = []
		self.calledFunctions = []

	def addCalledFunction(self, function):
		self.calledFunctions.append(function)

	def addArgument(self, argument):
		self.arguments.append(argument)

	def __str__(self):
		return self.name

	def toString(self):
		return (self.name + " (" + self.parentName + ")")

	def toStringDebug(self):
		return (self.name + str(self.calledFunctions))


def createSubgraph(inputFileName, subGraphName):
	if (verbose):
		print("Creating subgraph " + subGraphName + " from " + inputFileName)

	fileList, lineBreakIndexes = fileToList(inputFileName)
	nodes = findFunctions(subGraphName, fileList, lineBreakIndexes)
	return (subGraph(subGraphName, nodes))




#==========================================================================
#		File Parser
#==========================================================================

def fileToList(inputFileName):
	'''
	Converts a given file of source code into a list of string objects, for easier
	function parsing. Removes all comments and whitespace.
	Returns a list of strings.
	'''
	if (verbose):
		print(" Opening file " + inputFileName)

	inFile = open(os.path.abspath(inputFileName), 'r')
	try:
		inFile = open(os.path.abspath(inputFileName), 'r')
	except Exception as e:
		inFile.close()
		print (e)
		raise ValueError(("Unable to open " + inputFileName))

	if (verbose):
		print(" Converting " + inputFileName + " to list")
	
	totalFileList = []
	lineBreakIndexes = [0]

	for line in inFile:
		#Keep track of line break locations
		lineBreakIndexes.append(len(totalFileList))

		currentLine = line

		#Finds // comments in current line
		currentLine = currentLine.replace("//", "// ")
		index = currentLine.find("//")
		if (index != -1):
			if (not (currentLine.find("/*") < index)):
				currentLine = currentLine[0:index]

		#Replace certain characters for easier parsing
		currentLine = currentLine.replace("(", " ( ")
		currentLine = currentLine.replace(")", " ) ")
		currentLine = currentLine.replace("{", " { ")
		currentLine = currentLine.replace("}", " } ")
		currentLine = currentLine.replace("[", " [ ")
		currentLine = currentLine.replace("]", " ] ")
		currentLine = currentLine.replace(",", " , ")
		currentLine = currentLine.replace("\\", " @IGNOREQUOTE@ ")
		currentLine = currentLine.replace("\t", "")
		currentLine = currentLine.replace("\n", "")
		currentLine = currentLine.replace('"', ' @"@ ')
		currentLine = currentLine.replace('/*', ' @BEGINLONGCOMMENT@ ')	#makes long comments easier to find
		currentLine = currentLine.replace('*/', ' @ENDLONGCOMMENT@ ')	#makes long comments easier to find
		currentLine = currentLine.replace('*', ' * ')
		#currentLine = currentLine.replace('/', ' / ')
		currentLine = currentLine.replace('=', ' = ')
		currentLine = currentLine.replace('-', ' - ')
		currentLine = currentLine.replace('+', ' + ')
		currentLine = currentLine.replace('>', ' > ')
		currentLine = currentLine.replace('<', ' < ')

		
		currentLineList = currentLine.split(" ")
		currentLineList[:] = [x for x in currentLineList if x != '']

		for item in currentLineList:
			totalFileList.append(item)

	inFile.close()
	return totalFileList, lineBreakIndexes


def findFunctions(parentName, fileList, lineBreakIndexes):
	'''
	Locates and parses all function definitions within a given file.
	Returns all declared functions as a list of Node objects
	'''
	if (verbose):
		print(" Searching for function definitions in " + parentName)

	foundFunctions = []
	inComment = False
	inString = False

	for index in range(0, len(fileList), 1):
		if (fileList[index] == '@BEGINLONGCOMMENT@'):
			inComment = True
		if (fileList[index] == '@ENDLONGCOMMENT@'):
			inComment = False

		if (not inComment):
			if ((fileList[index] == '@"@') and (fileList[index-1] != "@IGNOREQUOTE@")):
				if (inString):
					inString = False
				else:
					inString = True

		if ((not inComment) and (not inString)):
			if (fileList[index] == '{'):
				if (fileList[index-1] == ')'):
					#Find which line the functions is defined on
					definitionLineNumber = 0
					for l in range(0, len(lineBreakIndexes), 1):
						if (lineBreakIndexes[l] > index-1):
							definitionLineNumber = l - 1
							break

					parseFunctionDefinition(parentName, fileList, index-1, foundFunctions, definitionLineNumber)

	return foundFunctions


def parseFunctionDefinition(parentName, fileList, index, foundFunctions, definitionLineNumber):
	'''
	Parses the function name, input arguments, and internally-called functions
	for a single given function definition.
	Constructs a Node object for the given function. Adds node o foundFunctions list
	'''

	tempIndex = index
	parenthesisCount = 0
	
	while True:
		tempIndex += -1

		if (fileList[tempIndex] == ')'):
			parenthesisCount += 1
		
		if (fileList[tempIndex] == '('):
			if (parenthesisCount == 0):
				#Extracts function name
				functionNameList = fileList[(tempIndex-1)].split("::")
				if (len(functionNameList)>1):
					functionName = sanitizeName(functionNameList[1])
					className = sanitizeName(functionNameList[0])
				else:
					functionName = sanitizeName(fileList[(tempIndex - 1)])
					className = False
				
				if (isNonStandardFunction(functionName)):
					newFunction = Node(functionName, parentName, definitionLineNumber, className)

					#Parses function input arguments
					arguments = fileList[tempIndex+1:index]

					i = 0
					for j in range(0, len(arguments), 1):
						if ((arguments[j] == ',') or (j == len(arguments)-1)):
							if (j == len(arguments)-1):
								newFunction.addArgument(arguments[i:j+1])
							else:
								newFunction.addArgument(arguments[i:j])
							i = int(j) + 1

					if (verbose):
						print("  Parsing definition: " + str(functionName) + "...")

					#Parse through function calls within definition
					newFunction.calledFunctions = list(set(parseFunctionCalls(fileList, index+1)))

					if (verbose):
						print("   Found " + str(len(newFunction.calledFunctions)) + " function calls in " + newFunction.name)
					#Add completed node to the list
					foundFunctions.append(newFunction)
				return
			else:
				parenthesisCount += -1


def parseFunctionCalls (fileList, startingIndex):
	'''
	Locates all function calls from within a given function definition
	starting at startingIndex.
	Returns a list of called function names (each element is a string)
	'''
	
	tempIndex = startingIndex
	braceCount = 0
	calledFunctions = []
	inComment = False
	inString = False

	while True:
		tempIndex += 1
		
		if (fileList[tempIndex] == '@BEGINLONGCOMMENT@'):
			if (not inString):
				inComment = True
		if (fileList[tempIndex] == '@ENDLONGCOMMENT@'):
			if (not inString):
				inComment = False

		if (not inComment):
			if ((fileList[tempIndex] == '@"@') and (fileList[tempIndex-1] != "@IGNOREQUOTE@")):
				if (inString):
					inString = False
				else:
					inString = True

		if ((not inComment) and (not inString)):
			#Checks for the end of function definition
			if (fileList[tempIndex] == '{'):
				braceCount += 1
			if (fileList[tempIndex] == '}'):
				if (braceCount == 0):
					return calledFunctions
				else:
					braceCount += -1

			#Checks for function calls
			if (fileList[tempIndex] == '('):
				if (isNonStandardFunction(fileList[tempIndex-1])):
					calledFunctions.append( sanitizeName( fileList[tempIndex-1].split(".")[-1] ) )


def isNonStandardFunction(name):
	'''
	Filters out standard function calls (like "if" or "printf"), as well as false alarms
	Returns True if given name is non-standard
	'''

	if (name == 'if'):
		return False
	if (name == 'while'):
		return False
	if (name == 'for'):
		return False
	if (name == 'printf'):
		return False
	if (name == 'strlen'):
		return False
	if (name == 'sizeof'):
		return False
	if (name == 'return'):
		return False
	
	if (name == '='):
		return False
	if (name == '=='):
		return False
	if (name == '!='):
		return False
	if (name == '>='):
		return False
	if (name == '<='):
		return False
	if (name == '>'):
		return False
	if (name == '<'):
		return False

	if (name == ','):
		return False
	if (name == '&'):
		return False
	if (name == '"'):
		return False

	if (name == '*'):
		return False
	if (name == '/'):
		return False
	if (name == '+'):
		return False
	if (name == '-'):
		return False

	if (name == '||'):
		return False
	if (name == '&&'):
		return False
	if (name == '('):
		return False
	if (name == ')'):
		return False
	
	if (name == 'LOG_PRINT'):
		return False
	if (name == 'switch'):
		return False

	return True




#==========================================================================
#		Commandline Argument Parsing
#==========================================================================

def parseConsoleCommands():
	'''
	Takes in console commands from user and provides usage help screen
	Initiates graph construction and rendering
	'''
	global verbose
	global lineNumbers

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=textwrap.dedent('''\
			FunctionFlow v1.02
			by Jose Rubianes

			FunctionFlow allows you to create function call graphs for an entire project
			directory. FF uses GraphViz for graph rendering.

			Prerequisites:
			  graphviz
			    $sudo apt-get install graphviz'''))

	#Required arguments
	parser.add_argument("InputDirectory", help = "Project Directory for which the call graph will be generated")
	parser.add_argument("outputFile", help="Name of output file. File extension shouldd be the same as the output format ('.ps' by default)")

	#Optional arguments
	parser.add_argument("-o", "--outputFormat", help="File format of the output. Use 'gv' for pure DOT code. Defaults to 'pdf'. More information at https://graphviz.gitlab.io/_pages/doc/info/output.html")
	parser.add_argument("-e", "--fileExtension", help="File type to generate call graphs for. Ignores all other file types. Used for specifing programming language of source code. Defaults to '.cpp'. *Currently only supporting C++")
	parser.add_argument("-f", "--filter", type=str, choices=["dot", "neato", "twopi", "circo", "fdp", "sfdp", "patchwork", "osage"], help="Filter used to generate the graph layout. Defaults to 'dot'. More information at https://graphviz.gitlab.io/_pages/pdf/dot.1.pdf")
	parser.add_argument("-c", "--cluster", action="store_true", help="Include if you want function definitions to be in discrete boxes based on file of declaration. Only valid for the 'dot' filter")
	parser.add_argument("-l", "--linenumbers", action="store_true", help="Include to add line numbers to graph")
	parser.add_argument("--exclusive", action="store_true", help="Include to only graph function calls when the called function is defined within the project directory")
	parser.add_argument("--verbose", action="store_true", help="Include to print debug statements into terminal")
	
	args = parser.parse_args()
	
	if (args.outputFormat):
		outFormat = args.outputFormat
	else:
		outFormat = "pdf"
	if (args.fileExtension):
		fileExtension = args.fileExtension
	else:
		fileExtension = ".cpp"
	if (args.filter):
		gFilter = args.filter
	else:
		gFilter = "dot"
	if (args.verbose):
		verbose = True
	if (args.linenumbers):
		lineNumbers = True


	#Translate source code into a .gv file
	translateDirectory(args.InputDirectory, fileExtension, "temp.gv", args.cluster, args.exclusive)

	if (verbose):
		print("Translation completed")

	#Render .gv file
	renderGraph("temp.gv", args.outputFile, outputFormat=outFormat, gFilter=gFilter, deleteInput=False)




#==========================================================================
#		Main entry point
#==========================================================================

if __name__ == "__main__":
   parseConsoleCommands()




############################################################################
#		Need to do
############################################################################
'''
-Parse class definitions and method calls
-handle "::" definitions
-add option to cluster class methods
-add support for multi-directory projects
-allow calls between clusters to be grouped into a single edge
'''
