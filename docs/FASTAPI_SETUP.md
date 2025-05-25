# FastAPI Setup Guide for Rocky Linux 9

## 🚀 **Quick Setup Commands**

### **1. Install Python and Dependencies**
```bash
# Update system
sudo dnf update -y

# Install Python 3.11+ and pip
sudo dnf install python3 python3-pip python3-venv -y

# Install development tools
sudo dnf groupinstall "Development Tools" -y
sudo dnf install python3-devel mysql-devel -y
```

### **2. Setup Project Directory**
```bash
# Create project directory
sudo mkdir -p /var/www/html/audipy
sudo chown $USER:$USER /var/www/html/audipy

# Navigate to project
cd /var/www/html/audipy

# Upload your code (git clone or scp)
# git clone https://github.com/yourusername/audipy.git .
```

### **3. Setup Python Virtual Environment**
```bash
# Create virtual environment
cd /var/www/html/audipy/backend
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_web.txt
```

### **4. Install Additional FastAPI Dependencies**
```bash
# Install FastAPI production server
pip install uvicorn[standard] gunicorn

# Install additional dependencies
pip install python-multipart python-jose[cryptography] passlib[bcrypt]
```

### **5. Test FastAPI Application**
```bash
# Test run (development)
cd /var/www/html/audipy/backend
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Test in browser: http://your-server-ip:8000
# API docs: http://your-server-ip:8000/docs
```

### **6. Create Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/audipy-api.service
```

**Service file content:**
```ini
[Unit]
Description=AudiPy FastAPI application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/html/audipy/backend
Environment=PATH=/var/www/html/audipy/backend/venv/bin
ExecStart=/var/www/html/audipy/backend/venv/bin/gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

### **7. Start and Enable Service**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start audipy-api

# Enable on boot
sudo systemctl enable audipy-api

# Check status
sudo systemctl status audipy-api

# View logs
sudo journalctl -u audipy-api -f
```

### **8. Configure Apache Virtual Host**
```bash
# Create vhost config
sudo nano /etc/httpd/conf.d/audipy.conf
```

**Apache configuration:**
```apache
<VirtualHost *:80>
    ServerName audipy.yourdomain.com
    DocumentRoot /var/www/html/audipy/frontend/dist
    
    # Serve React static files
    <Directory "/var/www/html/audipy/frontend/dist">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        # Handle React Router (SPA routing)
        FallbackResource /index.html
    </Directory>
    
    # Proxy API calls to FastAPI
    ProxyPreserveHost On
    ProxyPass /api/ http://127.0.0.1:8000/api/
    ProxyPassReverse /api/ http://127.0.0.1:8000/api/
    
    # Optional: Proxy docs for development
    ProxyPass /docs http://127.0.0.1:8000/docs
    ProxyPassReverse /docs http://127.0.0.1:8000/docs
    
    ErrorLog /var/log/httpd/audipy_error.log
    CustomLog /var/log/httpd/audipy_access.log combined
</VirtualHost>
```

### **9. Restart Apache**
```bash
# Test Apache config
sudo httpd -t

# Restart Apache
sudo systemctl restart httpd

# Enable Apache on boot (if not already)
sudo systemctl enable httpd
```

### **10. Setup SSL (Optional but Recommended)**
```bash
# Install Certbot
sudo dnf install certbot python3-certbot-apache -y

# Get SSL certificate
sudo certbot --apache -d audipy.yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

## 🔧 **Environment Configuration**

### **Backend .env file:**
```bash
# Create .env file
cd /var/www/html/audipy/backend
nano .env
```

**Required environment variables:**
```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=audipy
DB_USER=audipy
DB_PASSWORD=your_database_password

# Encryption
AUDIPY_MASTER_KEY=your_generated_master_key

# FastAPI
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=https://audipy.yourdomain.com,http://localhost:3000
```

### **Generate Secret Keys:**
```bash
# Generate JWT secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate master key (if not already generated)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 🔍 **Troubleshooting**

### **Check Service Status:**
```bash
# FastAPI service status
sudo systemctl status audipy-api

# View logs
sudo journalctl -u audipy-api -n 50

# Apache status
sudo systemctl status httpd

# Apache error logs
sudo tail -f /var/log/httpd/audipy_error.log
```

### **Test API Endpoints:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with domain
curl https://audipy.yourdomain.com/api/health
```

### **Common Issues:**

1. **Permission Errors:**
```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/html/audipy

# Fix permissions
sudo chmod -R 755 /var/www/html/audipy
```

2. **Port Already in Use:**
```bash
# Check what's using port 8000
sudo netstat -tulpn | grep :8000

# Kill process if needed
sudo kill -9 <PID>
```

3. **Database Connection Issues:**
```bash
# Test database connection
mysql -u audipy -p audipy -e "SELECT 1;"

# Check if MySQL is running
sudo systemctl status mysqld
```

## 📝 **Development vs Production**

### **Development Mode:**
```bash
# Run with auto-reload
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### **Production Mode:**
```bash
# Run with Gunicorn (via systemd service)
sudo systemctl start audipy-api
```

## 🔄 **Deployment Workflow**

1. **Update code** (git pull or upload)
2. **Install dependencies** if requirements changed
3. **Build frontend** (`npm run build`)
4. **Restart FastAPI service** (`sudo systemctl restart audipy-api`)
5. **Test endpoints** to ensure everything works

## 📊 **Monitoring**

### **Log Locations:**
- **FastAPI:** `sudo journalctl -u audipy-api`
- **Apache:** `/var/log/httpd/audipy_error.log`
- **System:** `/var/log/messages`

### **Performance Monitoring:**
```bash
# Check resource usage
htop

# Check disk space
df -h

# Check memory usage
free -h
```

This setup provides a production-ready FastAPI deployment that will work with your React frontend and existing database! 