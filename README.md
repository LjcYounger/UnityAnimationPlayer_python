# Unity Animation Player for Python

These scripts enable you to play smooth 2D/3D(maybe) Unity animations in Python.

It may be useful when you animate window labels.

In fact, it automatically interpolates all directions; I'm just sampling a subset in the AnimationPlayer.

## Usage

- Use `"python example.py"` to test the example(only 2D)
- Use `"python visualization.py"` to visualize T.anim (contains almost all Unity interpolation methods)

## Disadvantages

- Does not support weightMode, even when attempting to calculate it in the code
- It can only parse animations instead of editing them

## Contrast

![Contrast Image](contrast.jpg)
