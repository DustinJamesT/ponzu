# -- 
# --- class for creating messari-styled slides and charts 
# -- 

# == TABLE OF CONTENTS ================================= 
# --- 1.00 - imports
# --- 2.00 - class definition 
# ----- 2.01 - initialization 
# ----- 2.02 - build chart:                creates plotly fig object at self.fig   
# ----- 2.03 - build cateogry bar chart:   creates plotly fig object at self.fig 
# ----- 2.04 - create legend:              updates fig legend 
# ----- 2.05 - build legend values:        creates dicts of legend items for right-side numeric option 
# ----- 2.06 - write legend:               places legend items from 'build legend values' on slide 
# ----- 2.07 - save output:                creates chart png file
# ----- 2.10 - create slide:               logic coordinator. directs traffic to other functions 
# ----- 2.90 - error handling 
# ----- 2.91 - format legend item helper
# ======================================================= 

# IMPORTS (1.00)
# -- images 
from io import BytesIO
from turtle import tiltangle, title
from unicodedata import decimal, digit
from PIL import (
    Image,
    ImageFont,
    ImageDraw,
)
# -- dataframes and numerics
import pandas as pd
import numpy as np
import math

from datetime import date
from pyparsing import col

import requests

from copy import deepcopy

# -- plots 
import plotly.express as px  # -- note plotly express doesn't support secondary y axis: https://plotly.com/python/multiple-axes/

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# CLASS DEFINITION (2.00)
class messychart: 
  # 2.01 - initialization
  def __init__(self, df, theme = 'dark'):  
    # -- dataframe
    self.df = df

    today = date.today()
    self.filepath = 'new_chart' + today.strftime("%Y_%m_%d")
    self.raw_folder = False

    # -- slide text 
    self.name = ''
    self.title = ''
    self.subtitle = ''
    self.date = today.strftime('%B %d, %Y')
    self.note = ''
    self.source = ''

    # -- chart variables
    self.scale_factor = 4

    # -- chart 
    self.fig = None
    self.slide = None 

    # -- chart config 
    self.yaxis_title = ''
    self.xaxis_title = ''
    self.font_size = 20

    self.width = 1565 #1500 
    self.hieght = 705 #675 

    self.chart_xloc = 50 # -- defines x & y locations when printing raw chart on background
    self.chart_yloc = 60 #100 

    self.yxais_dollars = False  

    self.legend_items = [] # stores dict items for right-hand legend items with values 
    self.color_legend_chg = True 

    self.yaxis_fmt_dict = {
      'percentage': ".2%",
      'numeric': None
    }

    # -- color sets 
    self.color_sets = {
      'standard': {'main': ['#5B8EDC', '#8ED7E1', '#B5D987', '#F09837', '#ED6E69', '#9BBBEA', '#B9E6ED', '#D2E8B5', '#F5C174', '#F2A6A4'], 'secondary': '#A030E5'},
      'bright':   {'main': ['#231DC5', '#1B80F3', '#00D1FF', '#7000FF', '#A030E5', '#CE66FF', '#16B65F', '#00E778', '#59FFCD', '#FFC700', '#FFDD64', '#FFF384', '#F3B09B'],'secondary': '#FFC700'}, 
      'website':  {'main': ['#537FC6', '#C67F53', '#C653B4', '#B4C653', '#53C67F', '#5353C6', '#53B4C6', '#7F53C6', '#C6B453', '#C65353', '#537F7F', '#7A7A7A'], 'secondary': '#A030E5'}, 
      'sunrise':  {'main': ['#377CCB', '#2BB5D3', '#947BC7', '#C875C2', '#E18399', '#E8C2AD', '#EBAB70', '#ED9767', '#E1B61D', '#377CCB', '#2BB5D3', '#947BC7'], 'secondary': '#8151db'}, 
    }

    # -- slide config 
    self.colors = self.color_sets['sunrise']['main']
    self.secondary_color = self.color_sets['sunrise']['secondary']


    theme_dict = {
      'light': {
          'color_pallet': self.colors, # Main color pallet
          'border_color': '#232629', # off black
          'gridline_color': "#ECF0F4",  # light grey
          'text_color': "#232629",  # off black
          'title_color': "#1D1F22",  # basically black
          'subtext_color': "#A6B3C1",  # grey - used for sub title and for date
          'background_url': "https://github.com/DustinJamesT/supply_curves/blob/f940adff54e52ac13a577bb38554cffdf18b1221/Graphics/Messari_blank_light.png?raw=True", ##does not have all text (ie: Source:, Date as of:, etc.)
          'background_url_note': "https://github.com/DustinJamesT/supply_curves/blob/f940adff54e52ac13a577bb38554cffdf18b1221/Graphics/Messari_blank_light.png?raw=True"
        },
      'dark': {
          'color_pallet': self.colors, # Main color pallet
          'border_color': '#CFDBE7', # off white
          'gridline_color': "#3D434A",  # dark grey
          'text_color': "#CFDBE7",
          'title_color': "#F3F7FB",  # basically white
          'subtext_color': "#A6B3C1",  # grey - used for sub title and for date
          'background_url': "https://github.com/DustinJamesT/supply_curves/blob/37f01b8c561a926437c666ff0b4367ea8a51de43/Graphics/Dark_noise_nonote.png?raw=True",
          'background_url_note': "https://github.com/DustinJamesT/supply_curves/blob/f197032aefeda34961418b9dee6a30a81e62e083/Graphics/Dark_noise_note.png?raw=True",
          #'background_url': "https://github.com/DustinJamesT/supply_curves/blob/999cf7f1c660f817fa0faa833f77ed76255762ef/Messari_slide_clean.png?raw=True",
          #'background_url_note': "https://github.com/DustinJamesT/supply_curves/blob/999cf7f1c660f817fa0faa833f77ed76255762ef/Messari_slide_clean.png?raw=True",
        }
      }

    self.theme = theme_dict[theme] if theme in theme_dict.keys() else theme_dict['dark']

    messari_fonts = {
      "Montserrat-Bold": "https://github.com/DustinJamesT/supply_curves/blob/999cf7f1c660f817fa0faa833f77ed76255762ef/Montserrat-Bold.ttf?raw=True",  # https://fonts.google.com/specimen/Montserrat?query=monts
      "Montserrat-Reg": "https://github.com/DustinJamesT/supply_curves/blob/6df2a17cdd9c5011bf205abfe7e50d498622feb2/Graphics/Montserrat-Regular.ttf?raw=True",
      "Montserrat-SemiBold": "https://github.com/DustinJamesT/supply_curves/blob/e4fac393fca3d51ab22d30f2d9874334bb2b7412/Graphics/Montserrat-SemiBold.ttf?raw=True",
      "Open-Sans-Reg": "https://github.com/DustinJamesT/supply_curves/blob/d04f226559f7b5970160606b357701efe3214b47/OpenSans-Regular.ttf?raw=True",  # https://fonts.google.com/specimen/Open+Sans
      "Open-Sans-semiBold": "https://github.com/DustinJamesT/supply_curves/blob/01263a2b5fe88d376e3431668c155b1d208c80d3/OpenSans-SemiBold.ttf?raw=True",
      "Open-Sans-Italic": "https://github.com/DustinJamesT/supply_curves/blob/c7f0bf1c2cfab6382bb8ec1ad812d26dcc562cad/Graphics/OpenSans-Italic.ttf?raw=True",
    }

    self.fonts = {}
    for font, url in messari_fonts.items():
        font_request = requests.get(url)
        font_file = font_request.content

        self.fonts[font] = font_file
  
  # 2.02 - build timeseries figure 
  def create_timeseries(self, chart_type = 'line', axis_title = '', yaxis_data_type = 'numeric', yxais_dollars = False, secondary_column = '',
                              secondary_axis_title = '', secondary_data_type = 'numeric', secondary_digits = 0, digits = 0): 
    # -- error handling 
    chart_type = self.error_handling('chart_type', chart_type)
    yaxis_data_type = self.error_handling('yaxis_data_type', yaxis_data_type)
    digits = self.error_handling('digits', digits)
    secondary_data_type = self.error_handling('secondary_data_type', secondary_data_type)
    secondary_digits = self.error_handling('secondary_digits', secondary_digits)

    # -- define plot columns
    if secondary_column in self.df.columns:
      plot_cols = list(self.df.columns)
      plot_cols.remove(secondary_column)

    else:
      plot_cols = list(self.df.columns)
      print("! - warning - secondary column not in df") if len(secondary_column) > 0 else None 

    # -- define chart object 
    self.fig = go.Figure()
    
    if secondary_column in self.df.columns:
      self.fig = make_subplots(specs=[[{"secondary_y": True}]])

    # -- define chart type
    if chart_type == 'line':
      for i, col in enumerate(plot_cols): 
        self.fig.add_trace(go.Scatter(x= self.df.index, y= self.df[col], mode='lines', name = col, line=dict(color = self.colors[i], width= 4)))

    if chart_type == 'area': 
      for i, col in enumerate(plot_cols): 
        alpha = 0.9

        hex = self.colors[i].lstrip('#')
        rgb = str(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)))

        rgba = 'rgba' + rgb[:-1] + ', ' + str(alpha) + ')'

        self.fig.add_trace(go.Scatter(x= self.df.index, y= self.df[col], mode='lines', name = col, stackgroup='one', fillcolor= rgba , line=dict(color = self.colors[i], width= 0)))
    
    if chart_type == 'bar': 
      for i, col in enumerate(plot_cols): 
        self.fig.add_trace(go.Bar(x= self.df.index, y= self.df[col], name = col, marker_color = self.colors[i], marker_line_width= 0))

      self.fig.update_layout(barmode='stack', bargroupgap=0.0)#, bargap=0.3, 0)

    
    if secondary_column in self.df.columns:
      self.fig.add_trace(go.Scatter(x= self.df.index, y= self.df[secondary_column], mode='lines', name = secondary_column,
                          line=dict(color = self.secondary_color, width=4)),
                          secondary_y=True)

    # -- format axis
    self.fig.update_layout({'yaxis_tickprefix':"$"}) if yaxis_data_type == 'dollar' else self.fig.update_layout({'yaxis_tickprefix':""})

    self.fig.update_xaxes(
        showgrid=False,
        linecolor= self.theme['border_color']
    )

    if yaxis_data_type == 'percent': 
      tickformat = "." + str(digits) + "%"
    else:
      tickformat = None 

    self.fig.update_yaxes(
        gridcolor= self.theme['gridline_color'],
        linecolor= self.theme['border_color'],
        zeroline=False,
        tickformat=tickformat,
        title = axis_title#,
        #title_font = dict(family='Open Sans')
    )

    if secondary_column in self.df.columns:
      # -- set format
      if secondary_data_type == 'percent': 
        tickformat = "." + str(secondary_digits) + "%"
      else:
        tickformat = None 

      tickprefix = '$' if secondary_data_type == 'dollar' else ''

      self.fig.update_yaxes(title = secondary_axis_title, secondary_y=True, tickformat = tickformat, tickprefix = tickprefix, showgrid=False)#, tickangle = 180)
      # -- TODO set axis bounds -- need to update parameters to allow passing through. Needed for when want axis to match or percent charts to be max 100% 
      #self.fig.update_yaxes(range=[0, self.df[secondary_column].max() * 1.1], secondary_y=True)
    
    return None

  # 2.03 - build cateogry bar chart 
  def create_category_bar(self , bars_different_colors = True, yaxis_data_type = 'numeric', axis_title = '', digits = 0, stacked = False, x_col = '', y_col = '', color_col = ''): 

    # -- error handling 
    bars_different_colors = self.error_handling('bars_different_colors', bars_different_colors)
    yaxis_data_type = self.error_handling('yaxis_data_type', yaxis_data_type)
    digits = self.error_handling('digits', digits) 

    # -- create bars 
    if bars_different_colors == True:
        if stacked:
          self.fig = px.bar(self.df, x = x_col, y = y_col, color = color_col, color_discrete_sequence= self.colors)
        else:
          self.fig = px.bar(self.df, color=self.df.index, color_discrete_sequence= self.colors)

    elif bars_different_colors == False:
        self.fig = px.bar(self.df, color_discrete_sequence= self.colors)

    number_of_bars = len(self.fig.data)
    bar_range = range(0, number_of_bars, 1)
    range_list = list(bar_range)
    for i in range_list:
        self.fig.data[i]["marker"]['line']['width'] = 0

    # -- format axis
    self.fig.update_layout({'yaxis_tickprefix':"$"}) if yaxis_data_type == 'dollar' else self.fig.update_layout({'yaxis_tickprefix':""})
    
    self.fig.update_xaxes(
        showgrid=False,
        linecolor= self.theme['border_color']
    )

    if yaxis_data_type == 'percent': 
      tickformat = "." + str(digits) + "%"
    else:
      tickformat = None 

    self.fig.update_yaxes(
        gridcolor= self.theme['gridline_color'],
        linecolor= self.theme['border_color'],
        zeroline=False,
        tickformat=tickformat,
        title = axis_title#,
        #title_font = dict(family='Open Sans')
    )

    return None 

  # 2.04 - create legend 
  def create_legend(self, legend_layout = 'bottom', legend_title = '', calc_method = 'last', calc_days = 30, secondary_column = '', yxais_dollars = False, yaxis_data_type = 'numeric', digits = 0, show_secondary=True): 
    # -- error handling 
    legend_layout = self.error_handling('legend_layout', legend_layout)
    calc_days = self.error_handling('calc_days', calc_days)
    calc_method = self.error_handling('calc_method', calc_method)

    # -- define basic layouts 
    if legend_layout == 'bottom':
        self.fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'xaxis_title':None,
            #'yaxis_title':yaxis_title,
            'yaxis_categoryorder' : 'total ascending',
            'legend_title':legend_title,
            'font_color':self.theme['text_color'],
            'font_size': self.font_size,
            'width':self.width,
            'height':self.hieght,
            'legend_traceorder': "normal",
            'legend_orientation':"h", #needed for legend center bottom
            'legend_x':.5, #needed for legend center bottom
            'legend_xanchor':'center' #needed for legend center bottom
        })

    elif legend_layout == 'right':
        # -- resize plot width 
        self.width = 1510 if self.width > 1510 else self.width
        self.hieght = 720 if self.hieght < 720 else self.hieght

        self.fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'xaxis_title':None,
            #'yaxis_title':yaxis_title,
            'legend_title':legend_title,
            'font_color':self.theme['text_color'],
            'font_size':self.font_size,
            'width':self.width,
            'height':self.hieght
        })

    elif legend_layout == 'None' or legend_layout == 'right_values':
      self.hieght = 720 if self.hieght < 720 else self.hieght

      self.fig.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'xaxis_title':None,
            #'yaxis_title':yaxis_title,
            #'legend_title':legend_title,
            'font_color':self.theme['text_color'],
            'font_size':self.font_size,
            'width':self.width,
            'height':self.hieght,
            'showlegend': False
        })

    # -- right numeric layout 
    if legend_layout == 'right_values':
      # -- resize if too large 
      self.width = 1235 if self.width > 1235 else self.width
      self.fig.update_layout({'width': self.width})

      self.build_legend_values(legend_title = legend_title, calc_method = calc_method, calc_days = calc_days,  secondary_column = secondary_column, 
                               yxais_dollars = yxais_dollars, yaxis_data_type = yaxis_data_type, digits = digits, show_secondary=show_secondary)

    return None 

  # 2.05 - create numeric right legend 
  def build_legend_values(self,  legend_title = '', calc_method = 'last', calc_days = 30,  secondary_column = '', yxais_dollars = False, yaxis_data_type = 'numeric', digits = 0, show_secondary = True): 
    # -- insert title if provided 
    if len(legend_title) > 0: 
      self.legend_items.append({
        'title': True, 
        'name': legend_title, 
        'value': None,
        'change_label': None, 
        'per_change': None,
        'change_color': None,
        'label_color': None, 
        'x': 1245,
        'y': 116
      })
    
    
    # -- force the last method if percent value type 
    calc_method = 'last' if yaxis_data_type == 'percent' else calc_method

    # -- set days to 1 if using the last method
    sum_days = 1 if calc_method == 'last' else calc_days

    last_i = 0

    # -- define plot columns
    if secondary_column in self.df.columns:
      plot_cols = list(self.df.columns)
      plot_cols.remove(secondary_column)

    else:
      plot_cols = list(self.df.columns)

    # -- build legend items 
    for i, col in enumerate(plot_cols):
      if col != secondary_column: 
        # -- get the value 
        value = self.df[col].rolling(sum_days).sum().iloc[-1]

        # -- get percent change 
        percent_change = self.df[col].rolling(sum_days).sum().pct_change(calc_days, fill_method='ffill').iloc[-1]

        # -- format the value
        value_formatted = self.format_value(value, decimals = digits, data_type = yaxis_data_type, dollar_sign = yxais_dollars)

        # -- build period change label 
        change_label = str(calc_days) + 'd Change'

        # -- define percent chg color 
        try: 
          chg_color = '#5ECFAE' if percent_change > 0 else '#F6586B'
        except: 
          chg_color = self.theme['text_color']

        chg_color = chg_color if self.color_legend_chg else self.theme['text_color'] # -- override top default if turned off at global 

        # -- format percent change 
        percent_change = "N/A" if math.isnan(percent_change) else "{0:.1%}".format(percent_change)

        # -- build legend item 
        legend_item = {
          'title': False, 
          'name': col, 
          'value': value_formatted,
          'change_label': change_label, 
          'per_change': percent_change,
          'change_color': chg_color,
          'label_color': self.colors[i], 
          'x': 1245,
          'y': 165 + (i*64) # -- defines the top starting point of the legend and increments successive items down
        }

        self.legend_items.append(legend_item)
        last_i = i 

    # -- add item for secondary column if needed
    if secondary_column in self.df.columns and show_secondary: 
      # -- get the value 
      value = self.df[secondary_column].rolling(sum_days).sum().iloc[-1]

      # -- get percent change 
      percent_change = self.df[secondary_column].rolling(sum_days).sum().pct_change(calc_days, fill_method='ffill').iloc[-1]

      # -- format the value
      value_formatted = self.format_value(value, decimals = digits, data_type = yaxis_data_type)

      # -- build period change label 
      change_label = str(calc_days) + 'd Change'

      # -- define percent chg color 
      try: 
        chg_color = '#5ECFAE' if percent_change > 0 else '#F6586B'
      except: 
        chg_color = self.theme['text_color']

      chg_color = chg_color if self.color_legend_chg else self.theme['text_color']
      
      # -- format percent change 
      percent_change = "N/A" if math.isnan(percent_change) else "{0:.1%}".format(percent_change)

      # -- build legend item 
      legend_item = {
        'title': False, 
        'name': secondary_column, 
        'value': value_formatted,
        'change_label': change_label, 
        'per_change': percent_change,
        'change_color': chg_color,
        'label_color': self.secondary_color, 
        'x': 1245,
        'y': 165 + ((1+last_i)*64)
      }

      self.legend_items.append(legend_item)

    return None 

  # 2.06 - inserts numeric right legend values on slide 
  def write_legend_values(self):
    # - enlarge slide for crispness 
    self.slide = self.slide.resize((self.slide.size[0] * self.scale_factor, self.slide.size[1] * self.scale_factor), resample=Image.ANTIALIAS)

    draw = ImageDraw.Draw(self.slide)

    for legend_item in self.legend_items: 

      if legend_item['title'] == False: 
        # -- draw dot 
        r = 18
        ellipse_x = legend_item['x'] + 6
        ellipse_y = legend_item['y'] + 3
        draw.ellipse((ellipse_x*self.scale_factor, ellipse_y*self.scale_factor, (ellipse_x + r)*self.scale_factor, (ellipse_y+r)*self.scale_factor), fill = legend_item['label_color'], outline = legend_item['label_color'])

        # -- draw text items  
        # --- title
        font = ImageFont.truetype( BytesIO(self.fonts[ 'Open-Sans-semiBold' ]), 24*self.scale_factor)
        draw.text(((legend_item['x'] + 36)*self.scale_factor, legend_item['y']*self.scale_factor), legend_item['name'], fill= self.theme['text_color'], font=font, anchor ='lt')
        # --- number
        font = ImageFont.truetype( BytesIO(self.fonts[ 'Open-Sans-semiBold' ]), 26*self.scale_factor)
        draw.text(((legend_item['x'] + 312)*self.scale_factor, legend_item['y']*self.scale_factor), str(legend_item['value']), fill= self.theme['text_color'], font=font, anchor ='rt', align = 'right')
        # --- change period 
        font = ImageFont.truetype( BytesIO(self.fonts[ 'Open-Sans-Reg' ]), 18*self.scale_factor)
        draw.text(((legend_item['x'] + 36)*self.scale_factor, (legend_item['y']+30)*self.scale_factor), legend_item['change_label'], fill= self.theme['text_color'], font=font, anchor ='lt')
        # --- change value
        font = ImageFont.truetype( BytesIO(self.fonts[ 'Open-Sans-Reg' ]), 18*self.scale_factor)
        draw.text(((legend_item['x'] + 312)*self.scale_factor, (legend_item['y']+30)*self.scale_factor), legend_item['per_change'], fill= legend_item['change_color'], font=font, anchor ='rt', align = 'right')
      else: 
        # -- draw title 
        font = ImageFont.truetype( BytesIO(self.fonts[ 'Montserrat-Bold' ]), 26*self.scale_factor)
        draw.text(((legend_item['x'] + 36)*self.scale_factor, legend_item['y']*self.scale_factor), legend_item['name'], fill= self.theme['text_color'], font=font, anchor ='lt')
        # -- draw line separator 
        x = (legend_item['x'] + 36) * self.scale_factor
        y = 150 * self.scale_factor
        draw.line([(x,y), (x + 1100,y)], fill= (203, 216, 229, 180), width = 3)#self.theme['gridline_color']) #gridline_color

    # --- save the file in the output folder 
    self.slide = self.slide.resize((self.slide.size[0] // self.scale_factor, self.slide.size[1] // self.scale_factor), resample=Image.ANTIALIAS)
    self.slide.save(f'{self.filepath}.png')

    return None 

  # 2.07 - save output (creates chart)
  def save_output(self): 
    # -- write temporary raw file & load 
    if self.raw_folder: 
      i = self.filepath.rfind('/')
      raw_path = self.filepath[:i] + '/raw' + self.filepath[i:]
      self.fig.write_image(f'{raw_path}-raw.png')
      foreground = Image.open(f'{raw_path}-raw.png')

    else:
      self.fig.write_image(f'{self.filepath}-raw.png')
      foreground = Image.open(f'{self.filepath}-raw.png')
    
    # -- default date to today
    today = date.today()
    self.date = today.strftime("%b %d, %Y") if len(self.date) < 0 else self.date

    # -- define text
    text_data = {
        'title':    {'text': self.title,
                    'font': 'Montserrat-Bold','font_size': 42, 'x': 161, 'y':40, 'fill': self.theme['title_color']},
                
        'subtitle': {'text': self.subtitle,
                    'font': 'Open-Sans-Reg' ,'font_size': 24, 'x': 165, 'y':92, 'fill': self.theme['subtext_color']},
                
        'source':   {'text': self.source,
                    'font': 'Open-Sans-Reg','font_size': 20, 'x': 132, 'y':792, 'fill': self.theme['text_color']},
                
        'date':     {'text': self.date,
                    'font': 'Open-Sans-semiBold','font_size': 20, 'x': 1334, 'y':831, 'fill': self.theme['subtext_color']},
    }

    # -- load background depending on Note 
    if len(self.note) > 0: 
      # -- load background with Note text and insert note text
      response = requests.get(self.theme['background_url_note'])
      text_data['note'] = {'text': self.note,
                           'font': 'Open-Sans-Reg' ,'font_size': 20, 'x': 113, 'y':838, 'fill': self.theme['text_color']}
    
    else: 
      response = requests.get(self.theme['background_url'])

    # -- load background and initiate draw 
    background = Image.open(BytesIO(response.content))
    background.paste(foreground, (self.chart_xloc, self.chart_yloc), foreground)
    draw = ImageDraw.Draw(background)

    # -- draw text items
    for textfield, data in text_data.items():
        font = ImageFont.truetype(
            BytesIO(self.fonts[data["font"]]), data["font_size"]
        )
        draw.text((data['x'], data['y']), data['text'], data['fill'], font=font)

    # -- output chart 
    background.save(f'{self.filepath}.png')
    self.slide = background

    return None 

  # 2.10 - create slide - logic coordinator function 
  def create_slide(self, chart_type = 'line', axis_title = '', yaxis_data_type = 'numeric', yxais_dollars = False, secondary_column = '', secondary_axis_title = '', stacked = False, x_col = '', y_col = '', color_col = '',
                         digits = 0, legend_layout = 'bottom', legend_title = '', calc_method = 'last', calc_days = 30, secondary_data_type = 'numeric', secondary_digits = 0, show_secondary = True, bars_different_colors = True): 
    # -- error handling 
    chart_type = self.error_handling('chart_type', chart_type)

    # -- build chart
    timeseries_types = ['line', 'area', 'bar']

    if chart_type in timeseries_types: 
      self.create_timeseries(chart_type = chart_type, axis_title = axis_title, yaxis_data_type = yaxis_data_type, 
                            secondary_column = secondary_column, secondary_axis_title = secondary_axis_title, digits = digits, 
                            secondary_data_type = secondary_data_type, secondary_digits=secondary_digits, yxais_dollars = yxais_dollars)

    category_types = ['bar_category']

    if chart_type in category_types: 
      self.create_category_bar(bars_different_colors = bars_different_colors, yaxis_data_type = yaxis_data_type, axis_title = axis_title, digits = digits, stacked = stacked, x_col = x_col, y_col = y_col, color_col = color_col)

    # -- build legend 
    self.create_legend(legend_layout = legend_layout, legend_title = legend_title, calc_method=calc_method, calc_days=calc_days,   secondary_column = secondary_column, 
                               yxais_dollars = yxais_dollars, yaxis_data_type = yaxis_data_type, digits = digits, show_secondary = show_secondary)

    # -- output chart 
    self.save_output()

    # -- write legend if numeric 
    if legend_layout == 'right_values':
      self.write_legend_values()

    return None

  # 2.90 - error handling 
  def error_handling(self, var, value): 

    var_definitions = {
      'theme':                 {'type': '',   'options': ['dark', 'light'], 'default': 'dark'}, 
      'chart_type':            {'type': '',   'options': ['line', 'area', 'bar', 'bar_category'], 'default': 'line'},
      'yaxis_data_type':       {'type': '',   'options': ['numeric', 'dollar', 'percent'], 'default': 'numeric'},
      'digits' :               {'type': 0,    'options': [0, 1, 2, 3], 'default': 0},
      'legend_layout':         {'type': '',   'options': ['bottom', 'right', 'right_values', 'None'], 'default': 'bottom'},
      'calc_method':           {'type': '',   'options': ['last', 'sum'], 'default': 'sum'}, 
      'calc_days' :            {'type': 0,    'options': [1, 7, 14, 30, 90, 180, 270, 360], 'default': 30},
      'bars_different_colors': {'type': True, 'options': [True, False], 'default': True},
      'secondary_data_type':   {'type': '',   'options': ['numeric', 'dollar', 'percent'], 'default': 'numeric'},
      'secondary_digits' :     {'type': 0,    'options': [0, 1, 2, 3], 'default': 0},
    }

    # -- print warning statements 
    if var in var_definitions.keys():
      resp = ''
      return_value = value 

      if type(value) != type(var_definitions[var]['type']): 
        resp = '!  - warning - incorrect TYPE for ' + var + '. Type is: ' + str(type(var_definitions[var]['type']))
        resp = resp + '. options are: ' + str(var_definitions[var]['options'])
        resp = resp + '. Default is: ' + str(var_definitions[var]['default'])
        return_value = var_definitions[var]['default']
      
      elif value not in var_definitions[var]['options']: 
        resp = '! - warning - incorrect VALUE for ' + var + '. options are: ' + str(var_definitions[var]['options'])
        resp = resp + '. Default is: ' + str(var_definitions[var]['default'])
        return_value = var_definitions[var]['default']
      
      if len(resp) > 0:
        print(resp)

    else: 
      print('dustin - this var dont have an entry: ' + var)
      return_value = ''

    return return_value 

  # 2.91 - format legend values
  def format_value(self, value, decimals = 1, data_type = 'numeric', dollar_sign = False):
    # returns formatted values for legend - $9.3B for example 

    # -- format numeric numbers 
    if data_type == 'numeric' or data_type == 'dollar':
      denominations = {
        'billions':  {'abbrev': 'B', 'value': 1000000000}, 
        'millions':  {'abbrev': 'M', 'value': 1000000}, 
        'thousands': {'abbrev': 'k', 'value': 1000}, 
      }

      for denomination in denominations.values():
        if value // denomination['value'] < 1000 and value // denomination['value'] > 0 : 
          resp = round(value /denomination['value'], decimals)
          resp = int(resp) if decimals < 1 else resp 
          resp = str(resp) + denomination['abbrev']
          resp = '$ ' + resp if data_type == 'dollar' else resp 

          return resp 

      # -- return default
      resp = round(value, decimals)
      resp = int(resp) if decimals < 1 else resp 
      return resp

    # -- format percent 
    elif data_type == 'percent': 
      value = value * 100 
      value = round(value, decimals)
      value = int(value) if decimals < 1 else value 
      resp = str(value) + '%'

      return resp 


  # 2.92 - color theme options 
  def get_color_themes(self):
    return list(self.color_themes.keys()) 
  
  def set_color_theme(self, theme): 
    if theme in self.color_sets.keys():
      self.colors = self.color_sets[theme]['main']
      self.secondary_color = self.color_sets[theme]['secondary']
      return True 

    else:
      return False 
