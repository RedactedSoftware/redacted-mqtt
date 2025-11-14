AWS EC2 + Mosquitto Broker Setup (Full Command Runbook)
1. Create the EC2 Instance

Use Amazon Linux 2023 or Ubuntu 22.04 — both are chill, but I’ll assume Ubuntu.

Instance details:

t2.micro or t3.micro

8–20GB storage

Security group with only these inbound rules:

SSH: TCP 22 (BUT locked to your IP only)

MQTT: TCP 1883 (if using straight TCP)

Secure MQTT: TCP 8883 (if using TLS)

HTTP/HTTPS only if you need a dashboard

No commands here — just AWS console setup.

2. SSH In
ssh -i <your-key.pem> ubuntu@<EC2_PUBLIC_IP>

3. Update the Server
sudo apt update && sudo apt upgrade -y

4. Install Mosquitto + Tools
sudo apt install -y mosquitto mosquitto-clients


Enable the service:

sudo systemctl enable mosquitto
sudo systemctl start mosquitto


Check status:

sudo systemctl status mosquitto

5. Configure Mosquitto Securely
Create a configuration file
sudo nano /etc/mosquitto/conf.d/default.conf


Paste this as a minimum safe config:

listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
persistence true
persistence_location /var/lib/mosquitto/
log_type all


Save + exit.

6. Create MQTT User
sudo mosquitto_passwd -c /etc/mosquitto/passwd myuser


Restart the broker:

sudo systemctl restart mosquitto

7. (Optional) Enable TLS (Highly Recommended)

Generate certs:

sudo mkdir -p /etc/mosquitto/certs
cd /etc/mosquitto/certs
sudo openssl req -new -x509 -days 365 -nodes -out mqtt.crt -keyout mqtt.key


Adjust config:

sudo nano /etc/mosquitto/conf.d/default.conf


Add under your listener:

listener 8883
cafile /etc/mosquitto/certs/mqtt.crt
certfile /etc/mosquitto/certs/mqtt.crt
keyfile /etc/mosquitto/certs/mqtt.key


Restart:

sudo systemctl restart mosquitto

8. Test Broker Locally
mosquitto_pub -t "test/topic" -m "hello" -u "myuser" -P "<password>"
mosquitto_sub -t "test/#" -u "myuser" -P "<password>"

9. Open Security Group Ports (AWS Console)

Inbound rules should ONLY include:

1883 or 8883 (not both unless needed)

22 locked to your IP

Everything else closed.

10. Verify Remote Connection From Your Laptop

Subscribe:

mosquitto_sub -h <EC2_PUBLIC_IP> -t "test/topic" -u "myuser" -P "<password>"


Publish:

mosquitto_pub -h <EC2_PUBLIC_IP> -t "test/topic" -m "yo" -u "myuser" -P "<password>"


If you can see the message:
Congrats, MQTT is alive and thriving.

11. System Hardening (Basic but essential)

Firewall (if using UFW):

sudo apt install ufw -y
sudo ufw allow 22
sudo ufw allow 1883
sudo ufw allow 8883
sudo ufw enable


Disable root login:

sudo nano /etc/ssh/sshd_config


Set:

PermitRootLogin no
PasswordAuthentication no


Apply:

sudo systemctl restart ssh

12. Auto-Start Monitoring

Enable Mosquitto logs:

sudo journalctl -u mosquitto -f


To make your README feel complete, add:

Explanation of inbound/outbound security groups

Diagram (optional) of device → EC2 → database flow

Troubleshooting notes (common MQTT errors)
