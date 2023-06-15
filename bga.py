import struct
from PIL import Image

def BaseHeader(bgatype):
    f = open("output.lua", "w")
    f.write("local BGAOPTION = 1;\n")
    f.write("if PREFSMAN:GetPreference('BackgroundFitMode') == 'BackgroundFitMode_CoverDistort' then\n")
    f.write("	BGAOPTION = 2;\n")
    f.write("elseif PREFSMAN:GetPreference('BackgroundFitMode') == 'BackgroundFitMode_FitInside' then\n")
    f.write("	BGAOPTION = 1;\n")
    f.write("end;\n")
    f.write("-- BGAOPTION = 0;	--	4.3 RATIO WITHOUT BLACK BARS\n")
    f.write("-- BGAOPTION = 1;	--	4.3 RATIO WITH BLACK BARS\n")
    f.write("-- BGAOPTION = 2;	--	16.9 RATION(fullscreen)\n")
    f.write("\n")
    f.write("-------------THIS FILE WAS CREATED WITH NOBGA PARSER FOR PUMPSANITY-------------\n")
    f.write("\n")
    if bgatype == "42474100":
        f.write("-------------BGA TYPE: BGA1-------------\n")
    else:
        f.write("-------------BGA TYPE: BGA2-------------\n")
    f.write("local t = Def.ActorFrame\n")
    f.write("{\n")
    f.write("	OnCommand=function(self)\n")
    f.write("		if BGAOPTION == 0 or BGAOPTION == 1 then\n")
    f.write("			self:zoomx(1.5):zoomy(1.5):xy(160,0);\n")
    f.write("		else\n")
    f.write("			self:zoomx(2):zoomy(1.5):xy(0,0);\n")
    f.write("		end;\n")
    f.write("	end;\n")
    f.write("};\n")
    f.write("\n")
    f.close()

def BGA1(in_file):
    print("BGA1")
    # 64	spr name
    # 4		number of instructions
    #44		for instruction data	*	quantity of instructions
    offsetblock = [2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
    # 2		timing
    # 2 	end of group	01 false		00 true
    # 4		dest x
    # 4		dest y
    # 4		center x
    # 4		center y
    # 4		scale
    # 4		degress
    # 4		color red
    # 4		color green
    # 4		color blue
    # 4		color alpha
    
    allSPRList = []
    
    
    # read the entire .bga file
    while True:
        sprName = bytes.fromhex(in_file.read(64).hex()).decode('utf-8')
        blockNumber = int.from_bytes(bytes.fromhex(in_file.read(4).hex()), 'little')
        
        sprData = {}
        sprData['sprName'] = sprName.rstrip('\x00')
        sprData['blockNumber'] = blockNumber
        
        allBlockData = []
        for b in range(blockNumber):
            currentBlockData = []
            for o in range(len(offsetblock)):
                hexdata = in_file.read(offsetblock[o]).hex()
                if o == 0:  #little int
                    hexdata+="0000"                    
                    hexdata = struct.unpack("<i", bytearray.fromhex(hexdata))[0]
                elif o >= 2:  #little float
                    hexdata = struct.unpack("<f", bytearray.fromhex(hexdata))[0]
                currentBlockData.append(hexdata)
            allBlockData.append(currentBlockData)   
            
        sprData['blockData'] = allBlockData
        allSPRList.append(sprData)
        
        hexdata = in_file.read(1).hex()
        if len(hexdata) == 0:
            break
        else:
            in_file.seek(in_file.tell() - 1)
    
    # read each spr
    for spr in allSPRList:
        f = open(spr["sprName"], "r")
        sprType = f.readline()
        if sprType.split()[1].lower() == "ani":
            spr["type"] = "ani"
        elif sprType.split()[1].lower() == "tile":
            spr["type"] = "tile"
        elif sprType.split()[1].lower() == "pattern":
            spr["type"] = "pattern"
        else:
            spr["type"] = "uknown_type"
        # print(sprType)
        f.readline()    #NUM
        
        # spr image data
        allImageData = []
        while True:
            line = f.readline()
            if line.lower().startswith("t "):
                imageData = {}
                lineData = line.strip("\n").split(" ")
                lineData = [i for i in lineData if i]
                imageData["imageName"] = lineData[1]
                lineData = [i for j, i in enumerate(lineData) if j not in (0,1)]                
                imageData["coords"] = lineData
                im = Image.open(imageData["imageName"].split(".")[0] + ".png")
                # width, height = im.size
                # print(im.size)
                imageData["imageSize"] = im.size
                allImageData.append(imageData)
            if not line:
                # print(allImageData)
                spr["imageInfo"] = allImageData
                break
        
        f.close()
    
    print("end")
    f = open("output.lua", "a")
    intCounter = 0
    for spr in allSPRList:
        if spr["type"] == "ani":
            f.write("local State" + spr["sprName"].split(".")[0] + str(intCounter) + "=0;" + "\n")
            f.write("local Sleep" + spr["sprName"].split(".")[0] + str(intCounter) + "=0.1;" + "\n")
        f.write("----------------" + spr["sprName"] + "----------------\n")
        f.write("----------------" + spr["type"] + "----------------\n")
        f.write("t[#t+1] = Def.ActorFrame\n")
        f.write("{\n")
        f.write("   OnCommand=cmd(visible,false;")        
        sleep0 = spr["blockData"][0][0]
        f.write("sleep," + str(sleep0 / 60) + ";")
        f.write("queuecommand,'Animate0');\n")
        blockCount = len(spr["blockData"])
        sleepTime = 0 #here for the or empty instruction
        for b in range(blockCount):
            f.write("   Animate" + str(b) + "Command=function(self)\n")
            if b == 0:
                f.write("       self:visible(true):")
            else:
                f.write("       self:")
            valueX = spr["blockData"][b][2]
            valueY = spr["blockData"][b][3]
            centerX = spr["blockData"][b][4]
            centerY = spr["blockData"][b][5]
            zoom = spr["blockData"][b][6]
            rotationZ = spr["blockData"][b][7]*-1 if spr["blockData"][b][7] != 0 else spr["blockData"][b][7]
            colorR = spr["blockData"][b][8]
            colorG = spr["blockData"][b][9]
            colorB = spr["blockData"][b][10]
            colorA = spr["blockData"][b][11]
            # result1 = bytearray.fromhex(valueX)
            # result1 = struct.unpack("f", result1)
            # print(valueX)
            # print(float(bytes.fromhex));
            f.write("xy(" + str(valueX + centerX) + "," + str(valueY + centerY) + "):")
            f.write("zoom(" + str(zoom) + "):")
            f.write("diffuse(" + str(colorR) + "," + str(colorG) + "," + str(colorB) + "," + str(colorA) + "):")
            f.write("rotationz(" + str(rotationZ) + "):")
            if b == 0:
                f.write("rotationy(0):")
            if blockCount > 0:
                if b == blockCount - 1:
                    f.write("queuecommand('EndAnimation');\n")
                else:
                    f.write("queuecommand('Animate" + str(b + 1) + "');\n")
            
            # print(str(len(spr["imageInfo"])))
            if spr["type"] == "ani":
                if b < blockCount - 1:
                    sleepTime = (spr["blockData"][b + 1][0] - spr["blockData"][b][0]) / len(spr["imageInfo"]) / 60
                f.write("       Sleep" + spr["sprName"].split(".")[0] + str(intCounter) + "=" + str(sleepTime) + ";" + "\n")
                f.write("       MESSAGEMAN:Broadcast('AnimationStart" + spr["sprName"].split(".")[0] + str(intCounter) + "');\n");
            for s in range(len(spr["imageInfo"])):
                alignX = (centerX / float(spr["imageInfo"][0]["coords"][6]))
                alignY = (centerY / float(spr["imageInfo"][0]["coords"][7]))
                f.write("       self:GetChild('" + spr["sprName"].split(".")[0] + str(s) + "')")
                # f.write(":align(" + str(alignX) + "," + str(alignY) + ");")
                f.write(":align(" + str(alignX) + "," + str(alignY) + ");\n")
                
            f.write("   end;\n")
        
        # print("-")
        f.write("   EndAnimationCommand=cmd(visible,false);\n")
        
        for s in range(len(spr["imageInfo"])):
        # for image in spr["imageInfo"]:
            f.write("   LoadActor('" + spr["imageInfo"][s]["imageName"].split(".")[0] + ".png') .. \n")
            f.write("   {\n")
            f.write("       Name = '" + spr["sprName"].split(".")[0] + str(s) + "';\n")
            # print(spr["imageInfo"][s]["coords"][4])
            customTop = float(spr["imageInfo"][s]["coords"][4]) / spr["imageInfo"][s]["imageSize"][0]
            customLeft = float(spr["imageInfo"][s]["coords"][5]) / spr["imageInfo"][s]["imageSize"][1]
            customHeight = float(spr["imageInfo"][s]["coords"][6]) / spr["imageInfo"][s]["imageSize"][0]
            customWidth = float(spr["imageInfo"][s]["coords"][7]) / spr["imageInfo"][s]["imageSize"][0]
            
            
            f.write("       OnCommand=cmd(customtexturerect," + str(customTop) + "," + str(customLeft) + "," + str(customHeight) + "," + str(customWidth) + ";")
            f.write("blend,'BlendMode_Normal';")
            f.write("xy," + str(spr["imageInfo"][s]["coords"][0]) + "," + str(spr["imageInfo"][s]["coords"][1]) + ";setsize," + str(spr["imageInfo"][s]["coords"][2]) + "," + str(spr["imageInfo"][s]["coords"][3]))
            
            if spr["type"] == "ani":
                f.write(";visible,false);\n");
            else:
                f.write(");\n");
            if spr["type"] == "ani":
                f.write("       CheckForUpdateCommand=function(self)\n")
                f.write("           self:visible(false);\n")
                f.write("           if State" + spr["sprName"].split(".")[0] + str(intCounter) + " == " + str(s) + " then\n")
                f.write("               self:visible(true);\n")
                f.write("           end;\n")
                f.write("           self:sleep(Sleep" + spr["sprName"].split(".")[0] + str(intCounter) + "):queuecommand('CheckForUpdate');\n")
                f.write("       end;\n")
                f.write("       AnimationStart" + spr["sprName"].split(".")[0] + str(intCounter) + "MessageCommand=cmd(finishtweening;queuecommand,'CheckForUpdate');\n")
                f.write("       AnimationStop" + spr["sprName"].split(".")[0] + str(intCounter) + "MessageCommand=cmd(finishtweening);\n")
            f.write("   };\n")
        if spr["type"] == "ani":
            f.write("   Def.ActorFrame\n")
            f.write("   {\n")
            # f.write("       OnCommand=cmd();\n")
            f.write("       UpdateCommand=function(self)\n")
            f.write("          State" + spr["sprName"].split(".")[0] + str(intCounter) + " = State" + spr["sprName"].split(".")[0] + str(intCounter) + " + 1;\n")
            f.write("          if State" + spr["sprName"].split(".")[0] + str(intCounter) + " >= " + str(len(spr["imageInfo"])) + " then\n")
            f.write("             State" + spr["sprName"].split(".")[0] + str(intCounter) + " = 0;\n")
            f.write("             self:finishtweening();\n")
            f.write("          end;\n")
            f.write("          self:sleep(Sleep" + spr["sprName"].split(".")[0] + str(intCounter) + "):queuecommand('Update');\n")
            f.write("       end;\n")
            f.write("       AnimationStart" + spr["sprName"].split(".")[0] + str(intCounter) + "MessageCommand=cmd(finishtweening;queuecommand,'Update');\n")
            f.write("   };\n")
        
        f.write("};\n")
        
        intCounter += 1
        
        
            
        # print(spr["sprName"].split(".")[0])
        # print(str(len(spr["imageInfo"])))
        # print("\n")
    
    f.write("if BGAOPTION == 1 then\n")
    f.write("   t[#t+1] = Def.ActorFrame\n")
    f.write("   {\n")
    f.write("       Def.Quad\n")
    f.write("       {\n")
    f.write("           OnCommand=cmd(xy,-160,0;setsize,160,720;diffuse,0,0,0,1;align,0,0);\n")
    f.write("       };\n")
    f.write("       Def.Quad\n")
    f.write("       {\n")
    f.write("           OnCommand=cmd(xy,800,0;setsize,160,720;diffuse,0,0,0,1;align,1,0);\n")
    f.write("       };\n")
    f.write("   };\n")
    f.write("end;\n")
    f.write("return t;")
    f.close()
    # print(in_file.tell())
    # for om in offsetblock:
        # hexdata = in_file.read(om).hex()
        # allSprData.append(hexdata)
        # print(hexdata)
        # print(in_file.tell())
    
    
        # hexdata = in_file.read(1).hex()
        # if len(hexdata) == 0:
            # break
    # numberofblocks = int.from_bytes(bytes.fromhex(offsetmainList[3]), 'little')
    # while True:
    # numberofblocks = int.from_bytes(bytes.fromhex(offsetmainList[3]), 'little')
    # for x in range(numberofblocks):
        # for ob in offsetblock:
            # hexdata = in_file.read(ob).hex()
            # print(">" + hexdata.upper())
    

def BGA2():
    print("BGA2")

def HexView():
    offsetmain = [ 4, 12]
    offsetmainList = []
    # 4       bga type
    # 12      air
    
   
    
   
    with open("101.bga", 'rb') as in_file:
        for om in offsetmain:
            hexdata = in_file.read(om).hex()
            offsetmainList.append(hexdata)
            # print(">" + hexdata.upper())
        # print("next block") 
         
        BaseHeader(offsetmainList[0])
        if offsetmainList[0] == "42474100":
            BGA1(in_file)
        elif offsetmainList[0] == "42474132":
            BGA2()
        
        
        
        # f = open("output.lua", "a")
        # f.write("append content")
        # f.close()
                
HexView()