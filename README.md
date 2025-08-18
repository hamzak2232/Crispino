# Crispino Cafe — Enhanced POS System (FastAPI + SQLite)

A modern, feature-rich point-of-sale web application for cafes and restaurants:

## ✨ Key Features

### 🛒 **Enhanced POS Interface**
- **Smart Search**: Real-time search across all items and categories
- **Keyboard Shortcuts**: 
  - `Ctrl+K` - Focus search
  - `Ctrl+Enter` - Checkout
  - `Esc` - Clear cart
  - `1-9` - Quick add items
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Dark Mode**: Toggle between light and dark themes
- **Toast Notifications**: Real-time feedback for all actions
- **Quick Reprint**: Reprint last order with one click

### 📊 **Advanced Analytics & Reports**
- **Daily Sales Reports**: Complete breakdown of daily performance
- **Order History**: Search and view all past orders
- **Popular Items**: Track best-selling items over time
- **Payment Analytics**: Payment method breakdown
- **Real-time Updates**: Auto-refreshing reports

### 🔧 **Enhanced Admin Panel**
- **Menu Management**: Easy category and item management
- **Order Search**: Search orders by number, note, or items
- **Data Export**: Export all data in JSON format
- **Database Backup**: Create automatic backups
- **Settings Management**: Configure cafe name, tax rates, etc.

### 🖨️ **Printing System**
- **Customer Receipts**: Professional customer receipts
- **Kitchen Slips**: Detailed kitchen orders
- **Auto-printing**: Sequential printing workflow
- **Reprint Functionality**: Reprint any order instantly

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Printer (optional, for receipts)

### Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application**:
   ```bash
   python start.py
   ```
   
   Or manually:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open your browser**:
   - **POS Interface**: http://127.0.0.1:8000/
   - **Admin Panel**: http://127.0.0.1:8000/admin

## 📱 Using the POS

### Basic Operations
1. **Select Category**: Click category tabs to browse items
2. **Add Items**: Click items to add to cart
3. **Adjust Quantities**: Use +/- buttons or type numbers
4. **Add Notes**: Optional notes for special requests
5. **Payment**: Choose payment method and complete transaction
6. **Print**: Automatic printing of customer receipt and kitchen slip

### Advanced Features
- **Smart Search**: Type to search items across all categories
- **Keyboard Shortcuts**: Use shortcuts for faster operation
- **Quick Actions**: Access history, reports, and reprint from POS
- **Responsive Layout**: Optimized for touch devices

## 🔧 Admin Features

### Menu Management
- **Categories**: Add, edit, and organize menu categories
- **Items**: Manage prices, availability, and descriptions
- **Sorting**: Custom sort order for categories and items

### Reports & Analytics
- **Daily Reports**: View sales, revenue, and item performance
- **Order History**: Search and review all orders
- **Popular Items**: Track best-sellers over time
- **Payment Analytics**: Payment method breakdown

### Data Management
- **Backup**: Create database backups
- **Export**: Export all data in JSON format
- **Settings**: Configure cafe name, tax rates, etc.

## 🎨 User Interface

### Modern Design
- **Clean Interface**: Intuitive, modern design
- **Dark Mode**: Toggle between light and dark themes
- **Responsive**: Works on all screen sizes
- **Accessibility**: Keyboard navigation and screen reader support

### Enhanced UX
- **Real-time Feedback**: Toast notifications for all actions
- **Smooth Animations**: Polished interactions
- **Error Handling**: Clear error messages and validation
- **Loading States**: Visual feedback during operations

## 📊 API Endpoints

The system includes a REST API for integration:

- `GET /api/orders/recent` - Recent orders
- `GET /api/reports/daily` - Daily sales report
- `GET /api/orders/search` - Search orders
- `GET /api/orders/{number}` - Get order by number
- `GET /api/items/popular` - Popular items
- `POST /api/admin/backup` - Create backup
- `POST /api/admin/export` - Export data

## 🗄️ Data Storage

- **SQLite Database**: Local file-based storage
- **Auto-backup**: Automatic database backups
- **Data Export**: JSON export functionality
- **Migration Support**: Schema versioning

## 🔒 Security & Reliability

- **Input Validation**: Comprehensive validation
- **Error Handling**: Graceful error recovery
- **Data Integrity**: Transaction-based operations
- **Local Storage**: No internet required

## 🎯 Customization

### Easy Customization
- **Cafe Branding**: Customize cafe name and logo
- **Tax Rates**: Configurable tax percentages
- **Payment Methods**: Add custom payment options
- **Receipt Layout**: Customizable receipt templates

### Extensible Architecture
- **Modular Design**: Easy to extend and modify
- **API-First**: REST API for integrations
- **Plugin Support**: Architecture supports plugins
- **Database Schema**: Well-designed, extensible schema

## 📈 Performance

- **Fast Loading**: Optimized for speed
- **Efficient Queries**: Optimized database queries
- **Caching**: Smart caching for better performance
- **Responsive**: Works smoothly on all devices

## 🛠️ Development

### Project Structure
```
crispinoCafe2/
├── app/
│   ├── main.py          # FastAPI application
│   ├── db.py            # Database operations
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, images
├── data/                # Database and backups
├── requirements.txt     # Python dependencies
├── start.py            # Startup script
└── README.md           # This file
```

### Adding Features
The modular architecture makes it easy to add new features:
- **New API endpoints** in `app/main.py`
- **Database functions** in `app/db.py`
- **UI components** in templates and static files

## 🤝 Contributing

This is a production-ready POS system. Feel free to:
- Report bugs
- Suggest features
- Submit improvements
- Share feedback

## 📄 License

This project is open source and available under the MIT License.

---

**Crispino Cafe POS** - Making cafe operations simple, efficient, and enjoyable! ☕