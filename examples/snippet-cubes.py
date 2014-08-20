#! /usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier. All Rights Reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------
import numpy as np
from makecube import makecube
from glumpy import app, gl, glm, gloo
from glumpy.graphics.collection import BaseCollection

vertex = """
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

attribute float index;
attribute vec3 position;
attribute vec4 color;

varying vec4 v_color;

void main()
{
    v_color = color;
    vec4 pos = projection * view * model * vec4(position,1.0);
    gl_Position = <grid>;
}
"""

fragment = """
varying vec4 v_color;
void main()
{
    <clip>;
    gl_FragColor = v_color;
}
"""

Grid = gloo.Snippet("""
uniform float rows, cols;
varying float v_index;
vec4 cell(vec4 position, float index)
{
    v_index = index;

    float col = mod(index,cols) + 0.5;
    float row = floor(index/cols) + 0.5;
    float x = -1.0 + col * (2.0/cols);
    float y = -1.0 + row * (2.0/rows);
    float width = 0.95 / (1.0*cols);
    float height = 0.95 / (1.0*rows);
    vec4 P = position / position.w;
    P = vec4(x + width*P.x, y + height*P.y, P.z, P.w);
    return P*position.w;
}
""")

Clip = gloo.Snippet("""
uniform vec2 iResolution;
uniform float rows, cols;
varying float v_index;
void clip(float index)
{
    vec2 P = gl_FragCoord.xy;

    // mod doesn't plya well with 0
    float i = index+.00001;
    float col = mod(i,cols);
    float row = floor(i/cols);
    float width  = iResolution.x / cols;
    float height = iResolution.y / rows;
    float x = col * width;
    float y = row * height;
    float gap = 1.5;

    if( P.x < (x+gap))        discard;
    if( P.x > (x+width-gap))  discard;
    if( P.y < (y+gap))        discard;
    if( P.y > (y+height-gap)) discard;

}
""")


rows,cols = 3,3
window = app.Window(width=1024, height=1024, color=(0.30, 0.30, 0.35, 1.00))

# Build collection
dtype = [("position", np.float32, 3),
         ("normal",   np.float32, 3),
         ("texcoord", np.float32, 2),
         ("color",    np.float32, 4),
         ("index",    np.float32, 1)]
cubes = BaseCollection(vtype=dtype, itype=np.uint32)
V,I,_ = makecube()
C = np.zeros(len(V),dtype=dtype)
C[...] = V
for i in range(rows*cols):
    C["index"] = i
    cubes.append(vertices=C, indices=I)
cubes._build_buffers()
V = cubes._vertices_buffer
I = cubes._indices_buffer


@window.event
def on_draw(dt):
    global phi, theta
    window.clear()
    program.draw(gl.GL_TRIANGLES, I)
    theta += 0.5
    phi += 0.5
    model = np.eye(4, dtype=np.float32)
    glm.rotate(model, theta, 0, 0, 1)
    glm.rotate(model, phi, 0, 1, 0)
    program['model'] = model

@window.event
def on_resize(width, height):
    program['projection'] = glm.perspective(fovy, width / float(height), 1.0, 100.0)
    program['clip']['iResolution'] = width, height

@window.event
def on_mouse_scroll(x, y, dx, dy):
    global fovy
    fovy = np.minimum(np.maximum(fovy*(1+dy/100), 10.0), 179.0)
    program['projection'] = glm.perspective(fovy,
                                            window.width/float(window.height),
                                            1.0, 100.0)

@window.event
def on_init():
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_BLEND)


program = gloo.Program(vertex, fragment)
program.bind(V)
view = np.eye(4, dtype=np.float32)
model = np.eye(4, dtype=np.float32)
projection = np.eye(4, dtype=np.float32)
glm.translate(view, 0, 0, -5)
program['model'] = model
program['view'] = view
program['grid'] = Grid("pos", "index")
program['grid']["rows"] = rows
program['grid']["cols"] = cols
program['clip'] = Clip("v_index")
program['clip']["rows"] = rows
program['clip']["cols"] = cols

fovy = 45
phi, theta = 30, 20
app.run()