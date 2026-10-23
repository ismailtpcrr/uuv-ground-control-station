import zmq
import json
import time

def main():
    print("--- FAKE JETSON (UUV SIMULATOR) STARTED ---")
    
    # --- TEST SENARYOSU DEĞİŞKENİ ---
    # Baş Mimar, testi buradan yöneteceksin:
    # 50.0 yaparsan -> Pil yeterli, Jetson "Arm" talebini onaylar.
    # 15.0 yaparsan -> Pil düşük, Jetson "Arm" talebini reddeder!
    FAKE_BATTERY_LEVEL = 15
    #FAKE_BATTERY_LEVEL = 15
    
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    
    # --- ZIRHLAR ---
    socket.setsockopt(zmq.SNDHWM, 0) 
    socket.setsockopt(zmq.RCVHWM, 0) 
    socket.setsockopt(zmq.LINGER, 0) 
    
    try:
        socket.bind("tcp://*:5555")
    except zmq.error.ZMQError as e:
        print(f"\n[CRITICAL ERROR] Port 5555 might be busy! Error: {e}")
        print("Solution: Please wait 10-15 seconds and try again.")
        return
    
    print(f"Battery Level simulated at: %{FAKE_BATTERY_LEVEL}")
    print("Waiting for connection from Ground Control Station (Port: 5555)...")
    print("System ready. Motors on standby. Listening for data...\n")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    last_joy_state = None
    last_motor_states = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
    
    # Sistemin gerçek fiziksel durumunu tutan değişken
    actual_arm_state = False 
    previous_requested_arm = False # YENİ: Talebin sadece ilk anını yakalamak için

   # Sistemin gerçek fiziksel durumunu tutan değişken
    actual_arm_state = False 
    previous_requested_arm = False # YENİ: Talebin sadece ilk anını yakalamak için
    
    # --- YENİ MİMARİ ZIRH: ARDUSUB İNADI (TTL - Time To Live) ---
    warning_ttl = 0
    active_warning_msg = None
    active_warning_type = None

    while True:
        try:
            # YENİ: Her döngüde mesajı sıfırla. Sadece kriz anında doldurulacak.
            gcs_warning_message = None
            gcs_warning_type = None
            
            # YENİ: Eğer aktif bir uyarı varsa ve süresi bitmediyse, kargoyu yollamaya devam et!
            if warning_ttl > 0:
                gcs_warning_message = active_warning_msg
                gcs_warning_type = active_warning_type
                warning_ttl -= 1
            
            socks = dict(poller.poll(50))
            
            if socket in socks and socks[socket] == zmq.POLLIN:
                message = socket.recv_string()
                data = json.loads(message)

                ui_needs_update = False 

                if "motor_index" in data:
                    m_idx = data["motor_index"]
                    m_val = data["value"]
                    
                    if last_motor_states.get(m_idx) != m_val:
                        last_motor_states[m_idx] = m_val
                        ui_needs_update = True 
                        
                else:
                    fw_bk = data.get("forward_back", 0.0)
                    lf_rt = data.get("left_right", 0.0)
                    up_dw = data.get("up_down", 0.0)
                    yaw = data.get("yaw", 0.0)
                    requested_arm = data.get("armed", False) # GCS'den gelen TALEP
                    
                    # --- MİMARİ ZIRH: UÇUŞ ÖNCESİ KONTROL (PRE-ARM CHECK) ---
                    if requested_arm:
                        if FAKE_BATTERY_LEVEL > 20.0:
                            actual_arm_state = True
                        else:
                            actual_arm_state = False
                    else:
                        actual_arm_state = False
                        
                    # Terminalde reddedilmeyi SADECE TALEP İLK GELDİĞİNDE (Edge Trigger) bas:
                    if requested_arm and not previous_requested_arm and not actual_arm_state:
                         # YENİ: GCS'ye (UI) gidecek mesajı pakete koymak üzere hazırla
                         # Görsel kaymayı önlemek için ek boşluklarla terminale bas:
                         print("\n\n\n\033[K[DEBUG] GCS'den ARM talebi geldi! Reddediliyor ve kargo hazırlanıyor...")
                         
                         # ARDUSUB İNADI: Mesajı tek seferlik atma, GCS'nin göreceğinden emin olmak için kuyruğa al (10 döngü = 0.5 saniye)
                         active_warning_msg = "Low Battery: Arm Request Denied!"
                         active_warning_type = "CRITICAL"
                         warning_ttl = 10
                         
                    previous_requested_arm = requested_arm # Talebin güncel durumunu kaydet
                    
                    fw_bk, lf_rt = round(fw_bk, 2), round(lf_rt, 2)
                    up_dw, yaw = round(up_dw, 2), round(yaw, 2)
                    
                    current_joy_state = (fw_bk, lf_rt, up_dw, yaw, actual_arm_state)
                    
                    if last_joy_state is None or current_joy_state != last_joy_state:
                        last_joy_state = current_joy_state
                        ui_needs_update = True 

               # --- TERMINAL DASHBOARD RENDERER ---
                if ui_needs_update:
                    status_str = "POWER ON 🟢" if actual_arm_state else "POWER OFF 🔴"
                    j = last_joy_state if last_joy_state else (0.0, 0.0, 0.0, 0.0, False)
                    
                    line1 = f"\r\033[K[JOY] {status_str} | Forward-Back: {j[0]:5.2f} | Left-Right: {j[1]:5.2f} | Depth: {j[2]:5.2f} | Yaw: {j[3]:5.2f}"
                    motor_info = " | ".join([f"M{i+1}: %{val*100:>4.1f}" for i, val in last_motor_states.items()])
                    line2 = f"\n\033[K[MOTORS] {motor_info}\033[F"
                    
                    print(f"{line1}{line2}", end="", flush=True)

            # 2. GCS'YE "BEN HAYATTAYIM" MESAJI (TELEMETRİ) GÖNDER!
            telemetry = {
                "battery": FAKE_BATTERY_LEVEL, # GCS'nin görmesi için gerçek pili basıyoruz
                "depth": 12.4,
                "status": "OK",
                "voltage": 12.7,
                "armed": actual_arm_state, # <-- MÜHİM NOKTA: Gerçek durumu yolluyoruz
                "motors": last_motor_states  
            }
            
            # YENİ: Eğer bu döngüde bir hata mesajı oluştuysa, onu kargoya ekle (STATUSTEXT)
            if gcs_warning_message:
                telemetry["status_msg"] = gcs_warning_message
                telemetry["msg_type"] = gcs_warning_type

            socket.send_string(json.dumps(telemetry), flags=zmq.NOBLOCK)
            
        except zmq.error.Again:
            pass
        except KeyboardInterrupt:
            print("\nSimulation closing manually...")
            break
        except Exception as e:
            print(f"\n[WARNING] Data synchronization error: {e}")
            time.sleep(0.1)

if __name__ == "__main__":
    main()