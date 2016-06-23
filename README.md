# Cinema4D-Threejs-Exporter
Exporter for Cinema 4D to JSON format usable in Three.js

*Currently supports only Cinema 4D R17 (needs quaternions, can be solved by polyfill) and export is targeted at Three.js JSON format 3 of version r74.*

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
