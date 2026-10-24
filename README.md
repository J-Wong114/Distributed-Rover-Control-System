# Distributed-Rover-Control-System

A Python-based rover simulation built with FastAPI and HTML/CSS/JavaScript. The application provides a browser-based operator interface for configuring a simulated environment, placing mines, creating rovers, and executing rover commands.

# Features
- **Map Management:** View and resize a configurable 2D grid representing the rover's environment.
- **Mine Management:** Place mines on the grid and retrieve or delete mine records through the API.
- **Command Execution:** Simulate rover movement, turning, and mine-disarming operations.
- **REST API:** Expose endpoints for managing maps, mines, and rovers using FastAPI.
- **Web Interface:** Interact with the simulation through a browser-based operator interface.

# Implementation
The backend uses FastAPI to handle HTTP requests and manage the simulated environment. Pydantic models define the data structures for maps, mines, and rovers, while in-memory Python data structures maintain the current application state.

The rover simulation processes movement and turning commands, updates rover positions, and includes a SHA-256-based brute-force process to simulate mine disarming.

The frontend uses HTML, CSS, JavaScript, and Jinja2 templates to display the grid and provide controls for managing mines and rovers.
