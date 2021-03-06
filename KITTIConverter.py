import os
import xml.etree.ElementTree as ET
from VOCConverter import ToVOCConverter


class KITTItoVOCConverter(ToVOCConverter):
    '''
    In KITTI each image has its own label file with the same name and different extension
    Each label file has 1 line per label
    Each column is:

        #Values    Name      Description
        ----------------------------------------------------------------------------
            1      type         Describes the type of object: 'Car', 'Van', 'Truck',
                                   'Pedestrian', 'Person_sitting', 'Cyclist', 'Tram',
                                   'Misc' or 'DontCare'
            1      truncated    Float from 0 (non-truncated) to 1 (truncated), where
                                   truncated refers to the object leaving image boundaries
            1      occluded     Integer (0,1,2,3) indicating occlusion state:
                                   0 = fully visible, 1 = partly occluded
                                   2 = largely occluded, 3 = unknown
            1      alpha        Observation angle of object, ranging [-pi..pi]
            4      bbox         2D bounding box of object in the image (0-based index):
                                   contains left, top, right, bottom pixel coordinates
            3      dimensions   3D object dimensions: height, width, length (in meters)
            3      location     3D object location x,y,z in camera coordinates (in meters)
            1      rotation_y   Rotation ry around Y-axis in camera coordinates [-pi..pi]
            1      score        Only for results: Float, indicating confidence in
                                   detection, needed for p/r curves, higher is better.
    '''

    def __init__(self,imageFolder,sourceLabelFolder,outputLabelFolder):
        '''
        imageFolder: folder where all the images are
        sourceLabelFolder: path to folder where source data is saved
        outputLabelFolder: path where ouptut files are to be saved
        '''
        super().__init__(imageFolder,sourceLabelFolder,outputLabelFolder)

        self.imageFormat = ".png"
        self.database = "KITTI"

    def createXMLLabelFile(self,labelFileName):
        '''
        take in a KITTI label file for an image (labelFileName) and save out the Pascal VOC format label file
        '''
        with open(os.path.join(self.sourceLabelFolder,labelFileName), "r") as f:
            self.currentOutFile = os.path.join(self.outputLabelFolder,labelFileName[:labelFileName.rfind(".txt")] + ".xml")
            self.currentImageFile = labelFileName[:labelFileName.rfind(".txt")] + self.imageFormat

            labelXML = self.initializeXMLFile()
            for l in f.readlines():
                line = l.split(" ")
                objectLabel = self.createXMLLabel(line)
                labelXML.append(objectLabel)

        tree = ET.ElementTree(labelXML)
        tree.write(self.currentOutFile)

    def createXMLLabel(self,line):
        '''
        Create a xml style label for the line that is passed in. Return the xml data
        '''
        label = line[0]
        truncated = line[1]
        occluded = line[2]
        alpha = line[3]
        bboxLeft = line[4]
        bboxTop = line[5]
        bboxRight = line[6]
        bboxBottom = line[7]
        dimHeight = line[8]
        dimWidth = line[9]
        dimLength = line[10]
        locX = line[11]
        locY = line[12]
        locZ = line[13]
        roty = line[14]
        
        objectLabel = ET.Element("object")
        ET.SubElement(objectLabel,"name").text = label.lower()
        ET.SubElement(objectLabel,"truncated").text = truncated
        ET.SubElement(objectLabel,"occluded").text = occluded
        ET.SubElement(objectLabel,"alpha").text = alpha

        bndbox = ET.SubElement(objectLabel,"bndbox")
        ET.SubElement(bndbox,"xmin").text = bboxLeft
        ET.SubElement(bndbox,"ymin").text = bboxTop
        ET.SubElement(bndbox,"xmax").text = bboxRight
        ET.SubElement(bndbox,"ymax").text = bboxBottom

        dimensions = ET.SubElement(objectLabel,"dimensions")
        ET.SubElement(dimensions,"height").text = dimHeight
        ET.SubElement(dimensions,"width").text = dimWidth
        ET.SubElement(dimensions,"length").text = dimLength

        location = ET.SubElement(objectLabel,"location")
        ET.SubElement(location,"x").text = locX
        ET.SubElement(location,"y").text = locY
        ET.SubElement(location,"z").text = locZ

        ET.SubElement(objectLabel,"rotation_y").text = roty

        return objectLabel

    def convertDataset(self,verbose=False):
        '''
        Convert the entire dataset
        '''

        # find all the label files
        labelFiles = os.listdir(self.sourceLabelFolder)
        numLabels = len(labelFiles)
        labelFileNames = [i.split(".")[0] for i in labelFiles]
        labelFileNames = list(set(labelFileNames))
        assert numLabels == len(labelFileNames), "Repeated label files!"

        # find all image files
        imageFiles = os.listdir(self.imageFolder)
        imageFileNames = [i.split(".")[0] for i in imageFiles]

        # verify there is a label for each image and vise-a-versa
        imagesWithNoLabel = list(set(imageFileNames) - set(labelFileNames))
        labelsWithNoImage = list(set(labelFileNames) - set(imageFileNames))
        assert len(imagesWithNoLabel) == 0, "Images with no label file found: {}".format(imagesWithNoLabel)
        assert len(labelsWithNoImage) == 0, "Labels with no image found: {}".format(labelsWithNoImage)

        # call createXMLLabelFile() on each file
        counter = 0
        for label in labelFiles:
            counter += 1
            self.createXMLLabelFile(label)
            if verbose and counter%100==0:
                print("On image {}/{} {:.1f}% complete".format(counter,numLabels,float(counter)/float(numLabels)*100.))
        print("Finished converting {} labels!".format(numLabels))

        
