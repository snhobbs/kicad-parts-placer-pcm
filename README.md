# KiCAD Parts Placement PCM

![logo](icons/logo.svg)


![gui](gui.png)

+ KiCAD Plugin, Stand-alone GUI, & CLI

+ Blog Post: <https://maskset.net/kicad-parts-placer.html>

+ Exact batch placement of components in a layout
+ Groups the components allowing them to be moved and positioned as a group, easily ensuring exact alignment
+ Useful for:
  + Creating bed of nails tester
  + Positioning mechanically important parts
  + Maintaining a form factor across different designs
+ Essentially the same as this [Altium feature](https://www.altium.com/documentation/altium-designer/pcb-cmd-placecomponentsfromfileplacecomponentsfromfile-ad)

## Example Use: Pogo pin & test pad placement
The project at <https://github.com/snhobbs/kicad-parts-placer/tree/master/example/example-placement> shows an example use.
This takes a centroid file from an existing design which is edited for input.

![Config file from centroid](documents/config_placements.png)

A schematic is drawn up with matching reference designators:

![tester schematic](documents/example-placement.svg)

The schematic is exported to a PCB which will look like this:

![Exported PCB](documents/exported_board.png)

Running the script on this board with this command exports the following board with the components exactly aligned ready for layout. The group can be treated as a footprint, placed where ever is useful. During layout you only have to deal with a single coordinate as the position within the group is locked.

```{python}
kicad-parts-placer --pcb example-placement.kicad_pcb --config centroid-all-pos.csv --out example-placement_placed.kicad_pcb -x 117.5 -y 53
```

![Generated PCB](documents/placed_components_board.png)

## Uses
1. Matching Form Factor & Templates
2. Critical component placement
3. Keeping a symmetrical design symmetrical
4. Automating parts placement
5. Reuse of parts placement sections


## Procedure: Matching Form Factor & Templates
KiCAD templates are great but once you use one there are no guarantees that no components have moved. Use this plugin / tool to enforce the parts placement is correct.

1. Export the centroid file of the template being used or generate a new description from the required positions
2. Ensure the reference designators match in the new design
3. Update PCB from schematic (f8)
4. Run script which moves existing ref des to the location in config


## Notes
+ Place parts in pcb layout from a configuration table.
+ Allows writing a config script which fully defines the parts
+ Connections are made either by updating from a schematic or passing a netlist
+ Use example of schematic to pcb placement
+ All parts are grouped together, locking their relative placement
+ Internal configuration is a dataframe with ref des, label/value, footprint, position x, position y. Notes fields can be added for documentation generation.
+ A separate config object can be that could pull in a board outline, stackup, etc describing the board.
+ Position, rotation, & ref des are available in the centroid file, that avoids requiring the source board be kicad.
