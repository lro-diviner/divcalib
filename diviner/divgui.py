from traits.api \
    import HasTraits, List, Property, File, Instance, Bool, Range, \
        Button, Dict, String
from traitsui.api \
    import Item, Group, View, CheckListEditor,FileEditor, UItem
from chaco.api \
    import ArrayPlotData, Plot
from enable.component_editor import ComponentEditor
from numpy import arange, nan
import os
import diviner as d
import sys
from threading import Thread


class DivChanDet(HasTraits):
    c = Range(1,9)
    det = Range(1,21)
    plotted = Bool(False)
    def __call__(self):
        """Constructs boolean condition for picking channel and detector."""
        return '(df.c==' + str(self.c) + ') & (df.det==' + str(self.det) + ')'
    def get_jdates(self,df):
        return df.jdate[(df.c==self.c) & (df.det==self.det)]
    def get_data(self,df,datastr):
        data = df[datastr][(df.c==self.c) & (df.det==self.det)]
        data[data== - 9999.0] = nan
        return data
    def get_id(self):
        return str(self.c)+str(self.det).zfill(2)

class DivChannel(HasTraits):
    id = Range(1,9)
    d = dict([(i+1, False) for i in range(21)])

class DivGui ( HasTraits ):
    """ Define the main DivGui class. """
    fpath = File#,
                 # filter=['*.h5','*.tab','*.TAB'])
    no_of_ch = 9
    no_of_det = 21
    status = String
    cdet = DivChanDet(c=1, det=11)
    channels = Dict([(i+1, DivChannel(id=i+1)) for i in range(9)])
    plot = Instance(Plot)
    plotted = []
    plotbutton = Button(label='Plot')
    # Channel List
    checklist_c = List(editor = CheckListEditor(
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
        UItem('status',style='custom'),
        Item( '_'),
        # Item( 'checklist_det', style = 'custom',     label = 'Detectors' ),
        # Item( '_' ),
    )

    # The view includes one group per column formation.  These will be displayed
    # on separate tabbed panels.
    view1 = View(
        Item('fpath', label='Inputfile'),
        cl_ch_group,
        Item('plot', editor=ComponentEditor(), show_label=False),
        # UItem('plotbutton'),
        title     = 'DivGui',
        buttons   = ['OK' ],
        width=800, height=800,
        resizable = True
    )

    def _create_plot_component(self,channel):
        # series = d.get_channel_mean(self.df,'tb',channel)
        # series = self.df.groupby(['c','jdate'])['tb'].mean()[channel]
        # print(len(series.))
        self.add_status("Printing channel {0}".format(channel))
        x = self.df.jdate[(self.df.c==channel) & (self.df.det ==11)].values
        y = self.df.tb[(self.df.c==channel) & (self.df.det ==11)].values
        self.plotdata = ArrayPlotData(x=x, y=y)
        plot = Plot(self.plotdata)
        plot.plot(("x", "y"), type='scatter', color='blue')
        self.plot = plot

    def _checklist_c_changed(self, old, new):
        print(old,new)
        self._create_plot_component(int(new[-1]))

    def add_status(self,txt):
        print(txt)
        self.status += txt + '\n'

    def _fpath_changed(self,new):
        self.add_status('Loading new file...')
        Thread(target=self.fpath_changed, args=(new,)).start()

    def fpath_changed(self,new):
        print("Reading",new)
        ####
        ### FIX ME: nrows = 1000 for develepment
        ####
        self.df = d.read_div_data(new,nrows=35000)
        self.add_status("Done loading new file.")
        self.checklist_c=['1']


# Run the GUI (if invoked from the command line):
if __name__ == '__main__':
    if sys.platform == 'darwin':
        # workdir = os.path.join(os.environ['HOME'],'data','diviner')
        fname = '/Users/maye/data/diviner/201204090110_RDR.TAB'
    else:
        # workdir = '/luna1/maye'
        fname = '/luna1/maye/2009071500.h5'
    # Create the GUI:
    gui = DivGui(fpath=fname)
    gui.configure_traits()