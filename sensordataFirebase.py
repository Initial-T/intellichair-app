import serial
import firebase_admin
from firebase_admin import credentials, db
import time

# Initialize Firebase
cred = credentials.Certificate("C:\\Users\\Kusa\\Desktop\\newkey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://intellichair-3062e-default-rtdb.firebaseio.com/'
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
                    sensorData = [int(val) for val in sensorData]

                    # Assign forces
                    seatleftFront   = sensorData[0]  # A0
                    seatleftRear    = sensorData[1]  # A1
                    seatrightFront  = sensorData[2]  # A2
                    seatrightRear   = sensorData[3]  # A3
                    backrestLeft    = sensorData[4]  # A4
                    backrestRight   = sensorData[5]  # A5


                    backCushion = backrestRight + backrestLeft
                    gyattCushion = seatleftFront + seatleftRear + seatrightFront + seatrightRear

                    seatleftTotal = seatleftFront + seatleftRear + backrestLeft
                    seatrightTotal = seatrightFront + seatrightRear + backrestRight

                    if backCushion < 100 and gyattCushion >= 300:
                        seatStatus = "Leaning forward"
                    elif seatleftTotal >= 180 and seatrightTotal >= 180:
                        seatStatus = "Evenly seated"
                    elif seatleftTotal > seatrightTotal + 50:
                        seatStatus = "Leaning left"
                    elif seatrightTotal > seatleftTotal + 50:
                        seatStatus = "Leaning right"
                    else:
                        seatStatus = "No one is seated"

                    # Upload to Firebase
                    uploadData = {
                        'sensor_6': seatleftRear, 
                        'sensor_5': seatleftFront, 
                        'sensor_4': seatrightFront, 
                        'sensor_3': seatrightRear, 
                        'sensor_2': backrestRight,
                        'sensor_1': backrestLeft, 
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
