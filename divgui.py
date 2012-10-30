from traits.api \
    import HasTraits, List, Property, File, Directory, Instance
from traitsui.api \
    import Item, Group, View, CheckListEditor,FileEditor
from chaco.api \
    import ArrayPlotData, Plot
from enable.component_editor import ComponentEditor    
from numpy import arange
import os
import diviner as d

def get_cond(c,det):
    return '(df.c==' + c + ') & (df.det==' + det + ')'

class DivGui ( HasTraits ):
    """ Define the main DivGui class. """

    workdir = Directory(os.path.join(os.environ['HOME'],'data','diviner'))
    fpath = File('/Users/maye/data/diviner/',
                 filter=['*.h5','*.tab','*.TAB'])
    no_of_ch = 9
    no_of_det = 21
    selection = Property
    plot = Instance(Plot)
    # Channel List
    checklist_c = List( value=['1'], editor = CheckListEditor(
                               values = [str(i) for i in arange(no_of_ch)+1],
                               cols   = no_of_ch/2+1 ) )
    # Detectors List
    checklist_det = List( value=['11'], editor = CheckListEditor(
                               values = [str(i) for i in arange(no_of_det)+1],
                               cols   = no_of_det/2+1 ) )

    

    # CheckListEditor display with four columns:
    cl_ch_group = Group(
        Item( 'checklist_c', style = 'custom',   label = 'Channels' ),
        Item( '_' ),
        Item( 'checklist_det', style = 'custom',     label = 'Detectors' ),
        Item( '_' ),
        label = 'Channel and Detector choice'
    )

    # The view includes one group per column formation.  These will be displayed
    # on separate tabbed panels.
    view1 = View(
        Item('fpath', label='Inputfile'),
        cl_ch_group,
        Item('plot', editor=ComponentEditor(), show_label=False),
        title     = 'DivGui',
        buttons   = [ 'OK' ],
        width=500, height=500,
            resizable = True
    )

    def _checklist_c_changed(self):
        for c in self.checklist_c:
            for det in self.checklist_det:
                print get_cond(c,det)
    
    def _checklist_det_changed(self):
        for c in self.checklist_c:
            for det in self.checklist_det:
                print get_cond(c,det)
    
    def _fpath_changed(self):
        print "Reading",self.fpath
        # self.df = d.read_pds(self.fpath)
        # print self.df.columns
    def _get_selection(self):
        return '(df.c=='+self.checklist_c[0]+') & (df.det==' + \
                self.checklist_det[0]+')'
# Create the GUI:
gui = DivGui()

# Run the GUI (if invoked from the command line):
if __name__ == '__main__':
    gui.configure_traits()