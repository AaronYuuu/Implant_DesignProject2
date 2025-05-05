import math
import matplotlib.pyplot as plt

from load_cell_library import Load_Cell_Sensor
import time 
from gpiozero import LED


#only use these if on real machine
load_cell = Load_Cell_Sensor()
load_cell.begin() ##only use if using with REAL SENSOR
load_cell.set_calibration_factor(441.915625) #  set calibration factor
load_cell.set_zero_offset(50549.6875) #set zero offset 
val = load_cell.get_weight()


#for phhysical output device
#code for turning light on if physical raspberry pi connected
red_led = LED(11) #match with input on breadboard
yellow_led = LED(16) #match with breadboard

#turn both lights off to begin
red_led.off()
yellow_led.off()



##Objective 1, returning sensor data, measure weight and increment months
def sensor_data(months):
    val = load_cell.get_virtual_weight(0,0.5)
    ##val = load_cell.get_weight()
    months +=1
    return val,months


##Objective 2

##find forces for each month
def get_force(val): 
    g = 9.81 
    m = 59 
    n = val/10
#Calculation
    force = round(m*n*g,1)
    return force

##elastic modulus's
def elastic_modulus_Bone(months):
    age = 49 + months/12
    E_bone = round(-0.196*(age - 40) + 17,1)
    return E_bone

#tensile stress of bone and stem
def tensile_stress(force):
    #Measurements needed for bone and implant
    fem_offset = 30
    pi= math.pi
    M = force * fem_offset
    
    ##Measurements for bone
    dia_o = 26
    di = 14
    A_bone = (pi/4) *(dia_o**2 - di**2)
    I_bone = (pi/64) *(dia_o**4 - di**4)
    y_bone = 0.5 * dia_o
   
    ##Measurements for implant
    dia_s = 36 ##double check with cad team
    d_implant = 0.5*dia_s
    A_implant = (pi/4)*d_implant**2
    I_implant = (pi/64)*d_implant**4
    y_implant = 0.5*d_implant
    
    ##For bone
    bone_stress = round(-force/A_bone + (M*y_bone)/I_bone,1)

    ##For implant
    implant_stress = round(-force/A_implant + (M*y_implant)/I_implant,1)
    
    return bone_stress, implant_stress


##Calculating the resulting tensile stress in bone and implant
def resultant_stress(E_bone, tensile_bone, tensile_implant):
    E_s = 70 ## The elastic modulus of PEEK gave an imaginary number, so use this
    ratio = E_bone/(E_bone+E_s)

   #Bone calculations
    resultant_bone = round(tensile_bone * (3 * ratio)**0.25,1)
    
    #implant calculations
    resultant_implant = round(tensile_implant * (1 - 3 * ratio)**0.25,1)

    return resultant_bone, resultant_implant


##Objective 3
#Calculate the ultimate tensile strength of the bone
def ultimate_tensile_stress_bone(months, E_s, E_bone):
    E_ratio = math.sqrt(E_s / E_bone)
    x = months / 12 
    UTS_bone = round(175 / (1 + 0.05 * math.exp(0.06 * x * E_ratio)),1)
    return UTS_bone
 
#Calculate the fracture risk based on reduced tensile stress and ultimate tensile stress, used for output to lights
def fracture_risk(resultant_bone, UTS_bone):
    percentage_stress = (resultant_bone / UTS_bone) * 100
 
    if percentage_stress < 10:
        return "minor"
    elif 10 <= percentage_stress < 50:
        return "moderate"
 
    elif 50 <= percentage_stress < 100:
        return "high"
 
    else:
        return "very high"

##Objective 4
def visualize_fracture_risk(mths_postop, resultant_tensile_bone, tensile_stress):

#Define what is on the X and Y axis for each graph
    x = mths_postop
    y1 = resultant_tensile_bone
    y2 = tensile_stress
    
    #Plot elements
    plt.title("Stress vs Time Post-Surgery")
    plt.xlabel("Time (Years Post-Surgery)")
    plt.ylabel("Stress(MPa)")

    #legend for lines
    plt.plot(x, y1, color = "blue")
    plt.plot(x, y2, color = "red")
    plt.legend(["Resultant Tensile Stress in Bone (ores,b)", "Ultimate Tensile Strength of Bone (UTSb)"], loc="upper right")
    
    plt.show()

def main():
    #variables required for calculations
    months = 0
    E_s = 70 #elastic modulus of implant
    #Arrays used to plot data
    resultant_tensile_bone = []
    tensile_stresses = []
    mths_postop = []

    print("mths\tapplied load\tRes. stress, bone\tRes. stress, stem\tE, bone\t\tUTS, bone") #header for printed values
    i = 0
    while i < 360:
        v = load_cell.get_weight()
        if v > 0: #check if there is weight on the sensor, only if there is, i is incremented
            i+=1
            #use functions to solve for variables
            val,months = sensor_data(months)
            force = get_force(val)
            elastic_modulus_bone = elastic_modulus_Bone(months)
            tensile_bone, tensile_implant = tensile_stress(force)
            bone_resultant, implant_resultant = resultant_stress(elastic_modulus_bone, tensile_bone, tensile_implant)
            uts_bone =  ultimate_tensile_stress_bone(months, E_s, elastic_modulus_bone)
             
            #code for physical output to lights based on output from fracture risk function
            risk = fracture_risk(bone_resultant, uts_bone)
            if risk == "minor":
                yellow_led.on()
                
            elif risk =="moderate":
                yellow_led.on()
                time.sleep(0.1)
                yellow_led.off()
                time.sleep(0.1)
                
            elif risk == "high":
                yellow_led.off()
                red_led.on()
                
            elif risk == "very high":
                red_led.on()
                time.sleep(0.1)
                red_led.off()
                time.sleep(0.1)

            #add values calculated to array for axes
            resultant_tensile_bone.append(bone_resultant)
            mths_postop.append(months/12)
            tensile_stresses.append(uts_bone)

            #print out values to display
            print(str(months) + "\t"+ str(force) + "\t\t" + str(tensile_bone) +  "\t\t\t" + str(implant_resultant) + "\t\t\t"+ str(elastic_modulus_bone) + "\t\t" + str(uts_bone))

        time.sleep(0.25)  #time delay as reading through data              
    visualize_fracture_risk(mths_postop, resultant_tensile_bone, tensile_stresses) #plot data
