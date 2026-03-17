# 🏪 Supermarket Staff Scheduler

A sophisticated PyQt6-based application for optimizing supermarket staff scheduling with minimal cost while meeting demand requirements. Features an intuitive graphical interface for managing roles, costs, and shift planning.

## 📋 Features

- **Interactive GUI**: Modern PyQt6 interface with dark theme
- **Staff Role Management**: Add/remove roles with custom hourly costs
- **Demand Planning**: Visual demand tables for each hour of operation
- **Optimization Engine**: Minimizes total staffing costs while meeting requirements
- **Real-time Visualization**: Interactive charts showing staffing levels and costs
- **CSV Export**: Save scheduling results to CSV files
- **Flexible Hours**: Configurable opening and closing times
- **Role-based Staffing**: Different staff counts per role per hour

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Dependencies
```bash
pip install PyQt6 numpy matplotlib scipy
```

### Clone and Run
```bash
git clone https://github.com/idrissrb/supermarket-scheduler.git
cd supermarket-scheduler
python ihm_supermarche.py
```

## 💡 Usage

1. **Initial Setup**:
   - Enter your supermarket name
   - Configure staff roles and their hourly costs

2. **Configure Schedule**:
   - Set opening and closing hours
   - Input staff requirements for each hour and role
   - Adjust role costs if needed

3. **Optimize and View Results**:
   - Click "Résoudre" to calculate optimal staffing
   - View the schedule in the results panel
   - Hover over chart points for detailed information
   - Export results to CSV if needed

## 🏗️ Project Structure

```
supermarket-scheduler/
├── ihm_supermarche.py          # Main GUI application
├── supermarche/                # Core package
│   ├── __init__.py            # Package initialization
│   ├── dialogs.py             # Configuration dialogs
│   ├── solver.py              # Optimization algorithms
│   └── utils.py               # Helper functions and utilities
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔧 Technical Details

### Optimization Algorithm
The application uses linear programming to minimize total staffing costs while ensuring:
- Minimum staff requirements are met for each hour
- Role-specific constraints are satisfied
- Total cost is minimized

### GUI Framework
- **PyQt6**: Modern Python GUI framework
- **Matplotlib**: Data visualization and charting
- **NumPy**: Numerical computations
- **SciPy**: Scientific computing (optimization)

### Key Components

#### Main Window (`ihm_supermarche.py`)
- Central application window
- Manages all UI components
- Handles user interactions
- Displays results and charts

#### Dialogs (`supermarche/dialogs.py`)
- `StartDialog`: Initial configuration (name and roles)
- `RolesDialog`: Role management interface

#### Solver (`supermarche/solver.py`)
- `solve_schedule()`: Core optimization function
- Uses scipy.optimize for linear programming
- Returns optimal staffing solution

#### Utilities (`supermarche/utils.py`)
- HTML result formatting
- Hour range formatting
- Chart generation helpers

## 🎨 Interface Features

- **Dark Theme**: Modern, easy-on-the-eyes interface
- **Interactive Tables**: Double-click to edit demand values
- **Real-time Updates**: Charts update as you modify parameters
- **Hover Tooltips**: Detailed information on chart hover
- **Responsive Layout**: Adapts to window resizing

## 📊 Output Formats

### Schedule Results
- Hourly breakdown of required staff per role
- Total staff count per hour
- Total cost calculation
- Visual chart representation

### CSV Export
- Structured data format
- Compatible with spreadsheet applications
- Includes all scheduling details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Common Issues

**PyQt6 Import Error**
```bash
pip install PyQt6
```

**Optimization Fails**
- Ensure demand values are reasonable
- Check that opening time is before closing time
- Verify at least one role is configured

**GUI Doesn't Start**
- Ensure all dependencies are installed
- Check Python version (3.8+ required)
- Try running with `python3` instead of `python`

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the code comments for implementation details
3. Open an issue on GitHub

## 🔄 Version History

- **v1.0.0**: Initial release with full PyQt6 GUI and optimization engine

---

**Built with ❤️ using PyQt6, NumPy, and SciPy**</content>
<parameter name="filePath">/home/idriss/projet_ro/idriss_pb19_app3/README.md
