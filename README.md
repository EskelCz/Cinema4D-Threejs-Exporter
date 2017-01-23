# Cinema4D-Threejs-Exporter
Exporter for Cinema 4D to JSON format usable in Three.js

*Currently supports only Cinema 4D R17+ (needs quaternions, can be solved by polyfill) and export is targeted at Three.js JSON format 3 of version r80. Also Python 2.7 is required, which is bundled with the latest version of C4D.*

![Image preview](https://github.com/BlackDice/Cinema4D-Threejs-Exporter/blob/master/preview.png?raw=true)

**Currently supports these features:**
- Vertices
- Faces (triangles and quads)
- Normals (face and vertex)
- UV maps
- Bones
- Weights
- PRS animation
- Separation of multiple animations based on markers

**Missing:**
- Accepting null parent of joints
- Scale options
- Axis options
- Morph animations
- Baking of animation
- Takes
- Tests

**How to use:**

1. Close Cinema 4D.

2. Copy the contents or clone the repository into plugins folder of Cinema 4D.

3. Start Cinema 4D.

4. You should then find the plugin in menu > plugins > Three.js Exporter.

Optionally you can then move the button anywhere in the interface, with window > customization > customize palettes.
