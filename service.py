import xbmc
import xbmcaddon

if __name__ == '__main__':
    #clear lock flag
    xbmcaddon.Addon('script.cmcut.editor').setSetting(id='exec_lock', value='False')
        
