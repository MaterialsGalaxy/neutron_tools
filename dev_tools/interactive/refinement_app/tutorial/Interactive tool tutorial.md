
This tutorial follows the same refinement process in the GSASII tutorial [CW Neutron Powder fit for Yttrium-Iron Garnet](https://advancedphotonsource.github.io/GSAS-II-tutorials/CWNeutron/Neutron CW Powder Data.htm) and has been adapted for the use of our  interactive GSASII galaxy tool.
### Requirements

- make sure you are connected to the intranet and can access http://host-172-16-101-76.nubes.stfc.ac.uk/ to access the galaxy instance
- Ensure that you have created an account and have signed into this galaxy instance. 

### Step 1: Create a project file

- upload the **CIF file**, **GSAS powder data file** and **instrument parameter file** to Galaxy. 
- For this tutorial the files are:
	- CIF file: **galaxy demo YFeAl garnet.cif**
	- GSAS powder data file: **garnet.raw**
	- instrument parameter file: **inst_d1a.prm**
- input those files into the **GSASII Refinement Stage 1** tool under the **Tools under development** tab.
- set the scatter type to **Neutron**
- **run** the tool

### Step 2: Start the **interactive refinement demo** tool.

- under the **Interactive** tab, select the  **interactive refinement demo** tool and run it. 
- when it loads the page will change to say "There is an InteractiveTool result view available, Open". 
	- The interactive tool link will also appear in the interactive tools in the left hand menu of galaxy. 
	- also clicking the eye symbol on the entry in the galaxy history will take you to the interactive tool.
- The interactive tool will initially be empty with just the sidebar options. 

### Step 3: Load the project

-  In the left hand sidebar under **Load GSASII project**, use the selection box to select the project you want to load. This must be a **.gpx file**.
- Then press the **Load project** button. 
- in a few seconds the tool should load the project data and a plot from the first histogram in the project.
- the plot can be zoomed into and panned around using the hidden buttons in the top right hand side of the plot. These buttons become visible when the cursor is over the plot area.

### Step 4: Set constraints

- in the side bar in the selection box under **view project data** select **constraints**
- in the **constraints** page in the left column is the constraint builder. 
- the right column is a searchable, filterable table of constraint parameters to add to the constraint builder. 
- to add a constraint select the constraint type in the **constraint type** selection box. 
	- at the moment options are equivalence or equation constraints.

- select **equivalence**
- then select parameters **AUiso** for **Fe2** and **Al3** by holding **ctrl** and selecting the corresponding rows in the parameter table in the right column.
- the selected parameters will appear in the constraint builder table with coefficients 1.
	- the coefficient can be edited by double clicking the number in the coefficient column
 - In this tutorial we can keep the coefficients as 1.
 - then we click add constraint. 
 - The new constraint will now appear in the current constraints box.
 - repeat this for **AUiso** for **Al4** and **Fe5**

- then set the constraint type to **equation**
- and repeat for **Afrac** for the same pairs of atoms
	- the equation constraint at the moment automatically sets the total to 1
- there should now be 2 equivalence constraints and 2 equation constraints in the current constraints table.

- next we go back to the **sidebar** and press the **refine** button.
	- this will save the changed values to galaxy as a delta file. The changes will be applied to the project file in galaxy as part of the proceeding refinement
	- the refinement will then be performed in galaxy
- once completed, the new project will be loaded automatically into the interactive tool.
	- we should notice the plot changing and the selected project changing made clear by the change in the history id number
- then we proceed to the next step

###  Step 5: Refine atoms

- after setting the constraints we now have to refine the site fractions of the Fe and Al atoms. 
- in the sidebar press the **view Phase** button
- at the top of the main window select the **atoms** tab.
- here we can see a table of the atoms in the phase.
- **double click** the cell under the **refine column** in the **Fe2 row**.
- type **F** and press **enter**. this will move you to the next cell in the column
- type **F** and press **enter** 3 more times
- then press **save atom changes**
- then press **refine**
- the plot should now look much more aligned, but the peak heights are still off.
### Step 6: Refine atoms again

- staying in the **atoms** tab of the **phase page**, add **U** to all entries in the refinement column and also an **X** to the **O6** atom. 
- refinement flags can be any combination of F X and U ie {FU, XU, FX, FUX, U, F, X} 
- once again hit **save atom changes** and press **refine**

### Step 7: Refine instrument and sample parameters

- Finally under **view histogram data** in the sidebar, select **instrument parameters**.
- in this window we can see the current values of the parameters and change them. 
	- we can also select parameters to refine by clicking the selection box under **select instrument parameters to refine**
	- select **U** **V** and **W**
	- then press **save instrument parameters** 
- in the sidebar under **view Histogram data** select **Sample parameters**
	- this page works the same as instrument parameters
	- add **DisplaceX** and **DisplaceY** to the refinement and press **save sample parameters**
	- then press **Refine**.
	- the refinement is now complete. 
	- all the project files containing all the information about the workflow are saved in the galaxy history. 
	- we can now close the interactive tool by closing the tab in the browser
	- we then stop the tool running by going back to the galaxy instance **interactive tool** tab
	- select the **checkbox** on the left side of the row for the **interactive_refinement** tool
	- then press the **stop** button beneath the checkbox