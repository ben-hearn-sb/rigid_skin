# rigid_skin
Rigid skinning animation tools

The tool takes any number of input meshes, combines them and skins them to their parents at the click of a button.

Buttons:
Create Target Mesh:          Create a target mesh that you want to combine your objects to
Delete Target Mesh:          Deletes the selected target mesh
Mark To Target:              Mark your selected Maya mesh objects to the selected target mesh
Unmark From Target:          Unmark selected targeted objects from the target mesh
Retarget to selected root:   Retarget the selected target mesh to a newly selected root (for errors)
Skin Selection:              Skin the selected target meshes

Installation instructions:
- Download the project as a .zip
- Extract the project into your documents Maya folder, the end result should look like this:
	documents/maya/maya_version/scripts/rigid_skin/scripts and content
​- Restart Maya if you have not done so

- Go to your Maya script editor and type the following command:
	from rigid_skin import main
	main.main()

Save that script to your shelf and clicking it should boot the UI

Visit the following link to see the demo video:
https://www.youtube.com/watch?v=MLDRxdkP43E