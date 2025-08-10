# Collapsible Components

Reusable Apple-inspired collapsible sections for automation.html and operations.html with smooth animations, technical detail sections, and consistent design.

## Features

- 🎨 **Apple-inspired Design**: Clean, modern design following Apple's design principles
- ⚡ **Smooth Animations**: Spring-based animations with chevron rotation
- 📱 **Responsive**: Works beautifully on all screen sizes
- ♿ **Accessible**: Full keyboard navigation and ARIA support
- 🔧 **Technical Details**: Specialized styles for commands, outputs, and metrics
- 🚀 **Easy Integration**: Simple HTML structure with automatic initialization
- 📊 **Progress Bars**: Built-in progress visualization components
- 🎯 **Status Indicators**: Color-coded status badges (success, warning, error, info)

## Files

- `collapsible-components.css` - All styles for collapsible components
- `collapsible-components.js` - JavaScript functionality and utilities
- `collapsible-example.html` - Complete example demonstrating all features
- `COLLAPSIBLE_COMPONENTS_README.md` - This documentation

## Quick Start

### 1. Include the Files

Add the CSS and JavaScript files to your HTML:

```html
<link rel="stylesheet" href="collapsible-components.css">
<script src="collapsible-components.js"></script>
```

### 2. Basic HTML Structure

```html
<div class="collapsible-container">
    <div class="collapsible-header">
        <div class="collapsible-title">
            <div class="collapsible-icon">🔧</div>
            <span>Your Title Here</span>
        </div>
        <div class="collapsible-chevron"></div>
    </div>
    <div class="collapsible-content">
        <p>Your content goes here...</p>
    </div>
</div>
```

### 3. Automatic Initialization

The components are automatically initialized when the page loads. No additional JavaScript required!

## Advanced Usage

### Create Components Programmatically

```javascript
// Create a simple collapsible
const collapsible = CollapsibleUtils.create({
    title: 'Network Status',
    icon: '🌐',
    content: '<p>Network is operational</p>',
    expanded: false
});

document.body.appendChild(collapsible);
```

### Create Technical Details Sections

```javascript
const technicalContent = CollapsibleUtils.createTechnicalDetails({
    title: 'OSPF Configuration',
    commands: [
        'router ospf 1',
        'router-id 1.1.1.1',
        'network 192.168.1.0 0.0.0.255 area 0'
    ],
    outputs: [
        'OSPF process 1 started\nRouter ID set to 1.1.1.1'
    ],
    metrics: [
        { value: '3', label: 'Neighbors' },
        { value: '100%', label: 'Success Rate' }
    ],
    status: 'success'
});

const collapsible = CollapsibleUtils.create({
    title: 'Router Configuration',
    icon: '🔧',
    content: technicalContent
});
```

### Programmatic Control

```javascript
// Expand/collapse specific collapsible
collapsibleManager.expand('my-collapsible-id');
collapsibleManager.collapse('my-collapsible-id');

// Expand/collapse all
collapsibleManager.expandAll();
collapsibleManager.collapseAll();

// Check state
const isExpanded = collapsibleManager.isExpanded('my-collapsible-id');
```

## CSS Classes Reference

### Container Classes

- `.collapsible-container` - Main container
- `.collapsible-header` - Clickable header
- `.collapsible-content` - Collapsible content area
- `.collapsible-title` - Title section with icon
- `.collapsible-icon` - Icon container
- `.collapsible-chevron` - Animated chevron indicator

### Technical Detail Classes

- `.technical-details` - Container for technical information
- `.details-title` - Title within technical details
- `.command-block` - Styled command display with terminal-like appearance
- `.output-block` - Styled output display
- `.status-indicator` - Status badges (success, warning, error, info)

### Metrics and Progress

- `.metrics-grid` - Grid layout for metrics
- `.metric-item` - Individual metric container
- `.metric-value` - Large metric value
- `.metric-label` - Metric description
- `.progress-container` - Progress bar container
- `.progress-bar` - Progress bar track
- `.progress-fill` - Progress bar fill with animation

### State Classes

- `.active` - Applied to expanded headers
- `.expanded` - Applied to expanded content
- `.fade-in` - Animation class for content
- `.pulse` - Loading animation

## Data Attributes

- `data-expanded="true"` - Set initial expanded state
- `data-initialized="true"` - Automatically added when initialized

## Events

The collapsible components dispatch custom events:

```javascript
// Listen for expand events
document.addEventListener('collapsible:expand', (e) => {
    console.log('Expanded:', e.detail.id);
});

// Listen for collapse events
document.addEventListener('collapsible:collapse', (e) => {
    console.log('Collapsed:', e.detail.id);
});
```

## Integration Examples

### For automation.html

Add collapsible sections to show workflow details:

```html
<div class="collapsible-container">
    <div class="collapsible-header">
        <div class="collapsible-title">
            <div class="collapsible-icon">🚀</div>
            <span>Workflow Execution Details</span>
        </div>
        <div class="collapsible-chevron"></div>
    </div>
    <div class="collapsible-content">
        <div class="technical-details">
            <div class="details-title">Generated Configuration</div>
            <div class="status-indicator success">Applied</div>
            
            <div class="command-block">
                <code>interface GigabitEthernet0/0/1</code>
            </div>
            <div class="command-block">
                <code>ip address 192.168.1.1 255.255.255.0</code>
            </div>
            
            <div class="output-block">Configuration applied successfully
Interface is now up and operational</div>
        </div>
    </div>
</div>
```

### For operations.html

Add collapsible sections for operation details:

```html
<div class="collapsible-container">
    <div class="collapsible-header">
        <div class="collapsible-title">
            <div class="collapsible-icon">📊</div>
            <span>Network Diagnostics</span>
        </div>
        <div class="collapsible-chevron"></div>
    </div>
    <div class="collapsible-content">
        <div class="technical-details">
            <div class="details-title">Interface Status Check</div>
            <div class="status-indicator info">Monitoring</div>
            
            <div class="command-block">
                <code>show interface status</code>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">24</div>
                    <div class="metric-label">Active Ports</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">0</div>
                    <div class="metric-label">Errors</div>
                </div>
            </div>
        </div>
    </div>
</div>
```

## Animations

The components include several built-in animations:

- **Expand/Collapse**: Smooth height transitions with fade effects
- **Chevron Rotation**: 180-degree rotation with spring easing
- **Hover Effects**: Subtle scale and shadow changes
- **Progress Bars**: Shimmer effect on progress fills
- **Status Indicators**: Pulsing dot animations

## Customization

### CSS Custom Properties

The components use CSS custom properties for easy theming:

```css
:root {
    --apple-blue: #007AFF;
    --apple-gray-6: #F2F2F7;
    --border-radius-medium: 12px;
    --shadow-medium: 0 4px 20px rgba(0, 0, 0, 0.08);
    --transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}
```

### Status Colors

Customize status indicator colors:

```css
.status-indicator.custom {
    background: rgba(255, 0, 128, 0.1);
    color: #FF0080;
    border: 1px solid rgba(255, 0, 128, 0.3);
}
```

## Browser Support

- Modern browsers (Chrome 60+, Firefox 55+, Safari 12+, Edge 79+)
- Graceful degradation for older browsers
- Full touch support for mobile devices
- Keyboard navigation support

## Best Practices

1. **Use semantic HTML**: Ensure proper heading hierarchy
2. **Provide meaningful icons**: Choose icons that represent the content
3. **Keep content organized**: Use technical details for structured information
4. **Test keyboard navigation**: Ensure all functionality works with keyboard
5. **Consider performance**: Avoid too many expanded sections simultaneously

## Troubleshooting

### Common Issues

1. **Components not initializing**: Ensure both CSS and JS files are loaded
2. **Animations not smooth**: Check for CSS conflicts with transitions
3. **Content not showing**: Verify HTML structure matches examples
4. **Mobile issues**: Ensure viewport meta tag is present

### Debug Mode

Enable debug logging:

```javascript
// Add to console to see initialization logs
localStorage.setItem('collapsible-debug', 'true');
```

## Performance

- Minimal JavaScript footprint (~15KB)
- CSS animations use hardware acceleration
- Automatic cleanup of event listeners
- Efficient DOM manipulation

## License

These components are designed for use in the Multi-API Chat project and follow the same license terms.
