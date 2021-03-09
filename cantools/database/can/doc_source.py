import re, sys
import time
from decimal import Decimal

from ...version import __version__

from .c_source import Message

try:
    from si_prefix import si_format
    def pretty_number(x, u):
        if x is None: return "NA"
        return si_format(x, precision=0) + u
except:
    def pretty_number(x, u):
        if x is None: return "NA"
        return "%s%s" % (x, u)

RST_HEADER_FMT = '''\
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Descrizione dei dati del sistema {database_name} V{version}
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

{description}

.. contents:: Overview
   :depth: 3
   
{nodes_content}

'''

"""
rimossa intestazione, ora implementata in redmine
questo "output" viene assorbito dallo script ps1 e
incluso in pagina wiki main di redmine. 

h1. Descrizione dei dati del sistema {database_name} V{version}

{description}

{{{{toc}}}}
"""

RST_NODE_FMT = '''\
===================
Modulo {node_name}
===================

{node_description}

'''

RST_SIGNAL_FMT = '''\
#. {signal_name}

   {signal_description}
   
'''
   
RST_SIGNAL_TABLE_FMT = '''\
   +-------------+-------------+
   | Min         | Max         |
   +=============+=============+
   | {signal_min:11} | {signal_max:11} |
   +-------------+-------------+

   |

'''

RST_ALARM_FMT = '''\
#. Allarmi

   Lista allarmi
   
'''

RST_ALARM_TABLE_HEADER_FMT = '''\
   +--------------------------------------+------------------------------------------------+
   | Alarm                                | Description                                    |
   +======================================+================================================+
'''

RST_ALARM_TABLE_ROW_FMT = '''\
   | {signal_name:36} | {signal_description:46} |
   +--------------------------------------+------------------------------------------------+
'''

REDMINE_HEADER_FMT = '''\
{nodes_content}
'''

REDMINE_NODE_FMT = '''\

h2. Modulo {node_name}

{node_description}

'''

REDMINE_SIGNAL_FMT = '''\

h3. {signal_name}

{signal_description}'''
   
REDMINE_SIGNAL_TABLE_FMT = '''\

   |_. Min         |_. Max         |
   | {signal_min:11} | {signal_max:11} |

'''

REDMINE_ALARM_FMT = '''\

h3. Allarmi

Lista allarmi
'''

REDMINE_ALARM_TABLE_HEADER_FMT = '''\
   |_. Alarm                                |_. Description                                    |
'''

REDMINE_ALARM_TABLE_ROW_FMT = '''\
   | {signal_name:36} | {signal_description:46} |'''

"""
    return:
        all nodes RST content
"""
def _generate_rst_text(database_name, nodes):

    nodes_content = list()

    for node in nodes:
        signals_content = list()
        
        if not node.commented_signals: continue
        
        node_description = list()
        node_description.append(node.comment)
        node_description.append("")
        node_description.append("Il nodo gestisce i seguenti dati:\n")
        # for signal in node.commented_signals: node_description.append("- " + signal.snake_name)
        
        nodes_content.append(RST_NODE_FMT.format(
            node_name=node.name,
            node_description='\n'.join(node_description),
        ))
        
        alarms = list()
        for signal in node.commented_signals:
            comment = signal.comment.split('\n')
            signal_name = "**" + signal.name.strip() + "**: *" + comment[0].strip() + "*"
            signal_description=' '.join(comment[1:]).strip()
        
            if signal.length == 1: # if length=1 then it is an alarm (assumption...)
                alarms.append(signal)

            else:
                nodes_content.append(RST_SIGNAL_FMT.format(
                    signal_name=signal_name,
                    signal_description=signal_description,
                ))
            
                if signal._minimum != signal._maximum:
                    nodes_content.append(RST_SIGNAL_TABLE_FMT.format(
                        signal_min=pretty_number(signal._minimum, signal.unit),
                        signal_max=pretty_number(signal._maximum, signal.unit),
                        ))
                    
        if alarms:
            
            nodes_content.append(RST_ALARM_FMT.format(
                signal_name=signal_name,
                signal_description=signal_description,
            ))
            
            # in alarm table => put header only on first
            nodes_content.append(RST_ALARM_TABLE_HEADER_FMT.rstrip())

            for signal in alarms:
                nodes_content.append(RST_ALARM_TABLE_ROW_FMT.rstrip().format(
                    signal_name=signal.name,
                    signal_description=signal.comment
                    ))
            
        nodes_content.append("\n".join(signals_content))
    
    return '\n'.join(nodes_content)

"""
    return:
        all nodes REDMINE content
"""
def _generate_redmine_text(database_name, nodes):

    nodes_content = list()

    for node in nodes:
        signals_content = list()
        
        if not node.commented_signals: continue
        
        node_description = list()
        node_description.append(node.comment)
        node_description.append("")
        node_description.append("Il nodo gestisce i seguenti dati:\n")
        
        nodes_content.append(REDMINE_NODE_FMT.format(
            node_name=node.name,
            node_description='\n'.join(node_description),
        ))
        
        alarms = list()
        for signal in node.commented_signals:
            comment = signal.comment.split('\n')
            signal_name = signal.name.strip() # + "*: _" + comment[0].strip() + "_"
            signal_description="_" + comment[0] + "_"
            signal_description+="\n" + ' '.join(comment[1:]).strip()
        
            if signal.length == 1: # if length=1 then it is an alarm (assumption...)
                alarms.append(signal)

            else:
                nodes_content.append(REDMINE_SIGNAL_FMT.format(
                    signal_name=signal_name,
                    signal_description=signal_description,
                ))
            
                if signal._minimum != signal._maximum:
                    nodes_content.append(REDMINE_SIGNAL_TABLE_FMT.format(
                        signal_min=pretty_number(signal._minimum, signal.unit),
                        signal_max=pretty_number(signal._maximum, signal.unit),
                        ))
                    
        if alarms:
            
            nodes_content.append(REDMINE_ALARM_FMT.format(
                signal_name=signal_name,
                signal_description=signal_description,
            ))
            
            # in alarm table => put header only on first
            nodes_content.append(REDMINE_ALARM_TABLE_HEADER_FMT.rstrip())

            for signal in alarms:
                nodes_content.append(REDMINE_ALARM_TABLE_ROW_FMT.rstrip().format(
                    signal_name=signal.name,
                    signal_description=signal.comment
                    ))
            
        nodes_content.append("\n".join(signals_content))
    
    return '\n'.join(nodes_content)


def generate_rst(database,
             database_name,
             rst_name,
             encoding):
    """Generate Restructured Text from given CAN database `database`.

    `database_name` is used as a prefix for all defines, data
    structures and functions.

    `rst_name` is the file name of the RST file

    This function returns the RST files as strings.
    """

    date = time.ctime()
    nodes = database.nodes
    
    messages = [Message(message) for message in database.messages]
    
    for node in nodes:
        node.commented_signals = list()

    # Attach to message the node property
    for msg in messages:
        msg.node = next(n for n in nodes if n.name == next(iter(msg._senders or []), None))
        
        for signal in msg.signals:
            if (signal.comment):
                msg.node.commented_signals.append(signal)

    nodes_content = _generate_rst_text(
                   database_name,
                   nodes)
    
    rst_content = RST_HEADER_FMT.format(
                   version=__version__,
                   description=database.dbc._comment,
                   date=date,
                   database_name=database_name,
                   nodes_content=nodes_content
                   )

    print(rst_content)
    
    return rst_content


def generate_redmine(database,
             database_name,
             encoding):
    """Generate Textile Text from given CAN database `database`.
    `database_name` is used as a prefix for all defines, data
    structures and functions.
    This function returns the redmine files as strings.
    """

    date = time.ctime()
    nodes = database.nodes
    
    messages = [Message(message) for message in database.messages]
    
    for node in nodes:
        node.commented_signals = list()

    # Attach to message the node property
    for msg in messages:
        msg.node = next(n for n in nodes if n.name == next(iter(msg._senders or []), None))
        
        for signal in msg.signals:
            if (signal.comment):
                msg.node.commented_signals.append(signal)

    nodes_content = _generate_redmine_text(
                   database_name,
                   nodes)
    
    redmine_content = REDMINE_HEADER_FMT.format(
                   version=__version__,
                   description=database.dbc._comment,
                   date=date,
                   database_name=database_name,
                   nodes_content=nodes_content
                   )

    print(redmine_content)
    return redmine_content

