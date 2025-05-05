import serial
import firebase_admin
from firebase_admin import credentials, db
import time

# Initialize Firebase
<<<<<<< HEAD
cred = credentials.Certificate("path")
=======
cred = credentials.Certificate("C:\\Users\\Kusa\\Desktop\\newkey.json")
>>>>>>> 5cdd3eb (Pushing all code Currently)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'databaseURL'
})

# Connect to Arduino
ser = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)

def send_command(command):
    ser.write((command + '\n').encode())
    print(f"Sent command: {command}")

def read_data():
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"Received: {line}")
                sensorData = line.split(",")

                if len(sensorData) == 6:
                    sensorData = [max(0, min(100, int(val))) for val in sensorData]  

                    # sensor values
                    backrestLeft = sensorData[0]
                    backrestRight = sensorData[1]
                    seatrightFront = sensorData[2]
                    seatrightRear = sensorData[3]
                    seatleftFront = sensorData[4]
                    seatleftRear = sensorData[5]

                    seatLeft = seatleftFront + seatleftRear
                    seatRight = seatrightFront + seatrightRear
                    backTotal = backrestLeft + backrestRight
                    seatTotal = seatLeft + seatRight

                    # posture logic
                    if seatTotal == 0 and backTotal == 0:
                        seatStatus = "No one is seated"

                    else:
                        totalSensors = backrestLeft + backrestRight + seatrightFront 
                        + seatrightRear + seatleftFront + seatleftRear
                        
                        avg = totalSensors / 6
                        diff1 = abs(backrestLeft - avg)
                        diff2 = abs(backrestRight - avg)
                        diff3 = abs(seatrightFront - avg)
                        diff4 = abs(seatrightRear - avg)
                        diff5 = abs(seatleftFront - avg)
                        diff6 = abs(seatleftRear - avg)

                        if diff1 < avg * 0.2 and diff2 < avg * 0.2 and diff3 < avg * 0.2 and diff4 < avg * 0.2 and diff5 < avg * 0.2 and diff6 < avg * 0.2:
                            seatStatus = "Evenly seated"
                        elif backrestLeft < 10 and backrestRight < 10 and seatTotal > 50:
                            seatStatus = "Leaning forward"
                        elif seatrightFront + seatrightRear + backrestRight > (seatleftFront + seatleftRear + backrestLeft) * 1.2:
                            seatStatus = "Leaning right"
                        elif seatleftFront + seatleftRear + backrestLeft > (seatrightFront + seatrightRear + backrestRight) * 1.2:
                            seatStatus = "Leaning left"
                        else:
                            seatStatus = "Adjusting posture"

                    # Upload to Firebase
                    uploadData = {
                        'sensor_1': backrestLeft,
                        'sensor_2': backrestRight,
                        'sensor_3': seatrightFront,
                        'sensor_4': seatrightRear,
                        'sensor_5': seatleftFront,
                        'sensor_6': seatleftRear,
                        'seat_status': seatStatus
                    }

                    print("Uploading to Firebase:", uploadData)
                    ref = db.reference('pressure_data')
                    ref.update(uploadData)

    except Exception as e:
        print(f"Error reading data: {e}")

def main():
    send_command("start")
    while True:
        read_data()
        time.sleep(0.01)

if __name__ == '__main__':
    main()
<<<<<<< HEAD
=======

>>>>>>> 5cdd3eb (Pushing all code Currently)
