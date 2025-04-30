import serial
import firebase_admin
from firebase_admin import credentials, db
import time

# Initialize Firebase
cred = credentials.Certificate("pathway")
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
                    backrestLeft = sensorData[0]
                    backrestRight = sensorData[1]
                    seatrightFront = sensorData[2]
                    seatrightRear = sensorData[3]
                    seatleftFront = sensorData[4]
                    seatleftRear = sensorData[5]

                    backCushion = backrestRight + backrestLeft
                    gyattCushion = seatleftFront + seatleftRear + seatrightFront + seatrightRear

                    seatleftTotal = seatleftFront + seatleftRear + backrestLeft
                    seatrightTotal = seatrightFront + seatrightRear + backrestRight

                    if seatleftTotal >=150 and seatrightTotal >=150:
                        seatStatus = "Evenly seated"
                    elif seatleftTotal > seatrightTotal:
                        seatStatus = "Leaning left"
                    elif seatrightTotal > seatleftTotal:
                        seatStatus = "Leaning right"
                    elif backCushion == 0 and gyattCushion >= 200:
                        seatStatus = "Leaning forward"
                    else:
                        seatStatus = "Unknown seat status"

                    # Prepare Firebase upload
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
                    ref.set(uploadData)

    except Exception as e:
        print(f"Error reading data: {e}")

def main():
    send_command("start")
    while True:
        read_data()
        time.sleep(0.1)  # Match the Arduino delay

if __name__ == '__main__':
    main()
