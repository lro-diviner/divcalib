#  Copyright (c) 2007, Enthought, Inc.
#  License: BSD Style.# Imports:
from traits.api \
    import HasTraits, List

from traitsui.api \
    import Item, Group, View, CheckListEditor

from numpy import arange

# Define the demo class:
class CheckListEditorDemo ( HasTraits ):
    """ Define the main CheckListEditor demo class. """

    no_of_ch = 9
    no_of_det = 21
    # Define a trait for each of three formations:
    checklist_c = List( editor = CheckListEditor(
                               values = [str(i) for i in arange(no_of_ch)+1],
                               cols   = no_of_ch/2+1 ) )
    checklist_det = List( editor = CheckListEditor(
                               values = [str(i) for i in arange(no_of_det)+1],
                               cols   = no_of_det/2+1 ) )

    

    # CheckListEditor display with four columns:
    cl_ch_group = Group(
        Item( 'checklist_c', style = 'custom',   label = 'Channels' ),
        Item( '_' ),
        Item( 'checklist_det', style = 'custom',     label = 'Detectors' ),
        Item( '_' ),
        label = 'Ch and Det choice'
    )

    # The view includes one group per column formation.  These will be displayed
    # on separate tabbed panels.
    view1 = View(
        cl_ch_group,
        title     = 'CheckListEditor',
        buttons   = [ 'OK' ],
        resizable = True
    )

    def _checklist_c_changed(self):
        print self.checklist_c

# Create the demo:
demo = CheckListEditorDemo()

# Run the demo (if invoked from the command line):
if __name__ == '__main__':
    demo.configure_traits()