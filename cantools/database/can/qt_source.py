import sys
import time

from ...version import __version__

from .c_source import Message

QT_HEADER_FMT = '''\
/**
 * This file was generated by:
 * "{commandline}"
 * version {version} {date}.
 */

#ifndef {include_guard}
#define {include_guard}

#include <QObject>
#include <QVariant>
#include <QByteArray>

#include <{entity_frame_type}>
#include "{database_name}.h"
#include <QDebug>

#include <QTimer>
#include <QDateTime>

class {database_name}QtSignals;
class {database_name}QtMessage;

/*
 * Class declaration to declare a single signal exported
 * to Qt environment.
 */
class QVariantSignal{database_name} : public QObject
{{
    Q_OBJECT

    Q_PROPERTY(QVariant val WRITE send MEMBER m_val NOTIFY on_change)
    Q_PROPERTY(QVariant max MEMBER m_max CONSTANT)
    Q_PROPERTY(QVariant min MEMBER m_min CONSTANT)
    Q_PROPERTY(QVariant precision MEMBER m_precision CONSTANT)
    Q_PROPERTY(QString unit MEMBER m_unit CONSTANT)

    Q_PROPERTY({database_name}QtMessage* message MEMBER parent CONSTANT)

signals:
    void on_change(QDateTime t);

public:
    QVariantSignal{database_name}({database_name}QtMessage *parent, QVariant max, QVariant min, QVariant precision, QString unit) :
        parent(parent), m_val(QVariant()), m_max(max), m_min(min), m_precision(precision), m_unit(unit) {{}}

    {database_name}QtMessage *parent;
    QVariant m_val;
    const QVariant m_max, m_min, m_precision;
    const QString m_unit;

protected:
    virtual void send(QVariant x) = 0;
}};

/**
 * Class declaration to declare all signals exported
 * to Qt environment.
 */
class {database_name}QtMessage : public QObject
{{
    Q_OBJECT

    Q_PROPERTY(bool valid MEMBER m_valid NOTIFY on_valid)

signals:
    void on_valid(QDateTime t);

public:
    {database_name}QtMessage({specific_parameters_definitions} uint frameId, bool is_extended, uint length, uint cycle_time) : 
        {specific_parameters_initializations} m_frameId(frameId), m_length(length), is_extended(is_extended), m_cycle_time(cycle_time), m_valid(false) {{}}

public:
    {specific_parameters_declarations}
    const uint m_frameId;
    const uint m_length;
    const bool is_extended;
    const uint m_cycle_time;
    qint64 m_timestamp;
    bool m_valid;

public:

    void send_frame(QByteArray payload, bool is_extended);
    
    virtual void received(const {entity_frame_type} &frame) = 0;
    void check_exipiration_timestamp(qint64 now) {{
        // qDebug() << m_cycle_time << "," << now - m_timestamp;
        if ((m_cycle_time > 0) && (now - m_timestamp > m_cycle_time)) {{
            if (m_valid) {{
                m_valid = false;
                emit on_valid(QDateTime::fromMSecsSinceEpoch(m_timestamp));
            }}
        }}
    }}
}};

/*
 * Class declaration to manage all persistent signals exported
 * to Qt environment.
 */
class QVariantHistorySignal{database_name}: public QVariantSignal{database_name} {{

    Q_OBJECT

private slots:
    void update(QDateTime t);
    void update_valid(QDateTime t);

public:
    QVariantHistorySignal{database_name}({database_name}QtMessage *p, QVariant max, QVariant min, QVariant precision, QString unit) :
        QVariantSignal{database_name}(p, max, min, precision, unit) {{
        QObject::connect(this, &QVariantHistorySignal{database_name}::on_change, this, &QVariantHistorySignal{database_name}::update);
        QObject::connect(this->parent, &{database_name}QtMessage::on_valid, this, &QVariantHistorySignal{database_name}::update_valid);
    }}

    QList<QPair<QDateTime, QVariant>> m_data;
}};

{signals_classes_declarations}

/**
 * Class declaration to declare all signals exported
 * to Qt environment.
 */
class {database_name}QtMessages;
class {database_name}QtSignals : public QObject
{{
    Q_OBJECT

    {signals_properties}

private:
    {database_name}QtSignals(QObject * = nullptr);

public:
    static {database_name}QtSignals& instance() {{
        static {database_name}QtSignals * _instance = nullptr;
        if ( _instance == nullptr ) {{
            _instance = new {database_name}QtSignals();
        }}
        return *_instance;
    }}

    {signals_variables}

}};

{messages_classes_declarations}

/**
 * Class that groups all messages
 */
class {database_name}QtMessages : public QObject
{{
    Q_OBJECT

signals:
    void sendFrame(const {entity_frame_type} &frame) const;

private:
    {database_name}QtMessages(QObject * = nullptr) {{

{messages_instantations}

    }}

public slots:
    void periodic_check_validity() {{
        qint64 now = QDateTime::currentMSecsSinceEpoch();
        // qint64 deltat = now - m_timestamp;

{messages_check_validity}
    }}

public:
    QMap<uint, {database_name}QtMessage*> map;
    static {database_name}QtMessages& instance() {{
        static {database_name}QtMessages * _instance = nullptr;
        if ( _instance == nullptr ) {{
            _instance = new {database_name}QtMessages();
        }}
        return *_instance;
    }}

    void can_receive_frame_callback(const {entity_frame_type} &frame);

}};

#endif // close {include_guard}
'''

QT_SIGNALS_SEND_METHODS_FMT = '''\
void QVariantSignal_{signal_name}::send(QVariant x) {{
    static_cast<{database_name}QtMessage_{message_name}*>(parent)->store.{signal_name} = static_cast<{type_name}>(x.{variant_cast}());
    uint8_t dst_p[{message_length}];
    {database_name}_{message_name}_pack(dst_p, &(static_cast<{database_name}QtMessage_{message_name}*>(parent))->store{message_length_parameter});
    parent->send_frame(QByteArray(reinterpret_cast<char*>(dst_p), {message_length}), {message_is_extended});
}}
'''

QT_SIGNALS_RECEIVED_CODE_FMT = '''\
        x = {database_name}_{message_name}_{signal_name}_decode(store.{signal_name});
        if (signals_store.m_{signal_name}->m_val != x) {{
            emit signals_store.m_{signal_name}->on_change(QDateTime::fromMSecsSinceEpoch(m_timestamp));
            qDebug() << hex << "m_{signal_name}=" << signals_store.m_{signal_name}->m_val;
        }}
'''

QT_SIGNALS_RECEIVED_CODE_WITHOUT_ENCDEC_FMT = '''\
        if (signals_store.m_{signal_name}->m_val != store.{signal_name}) {{
            emit signals_store.m_{signal_name}->on_change(QDateTime::fromMSecsSinceEpoch(m_timestamp));
            qDebug() << hex << "m_{signal_name}=" << signals_store.m_{signal_name}->m_val;
        }}
'''

QT_MESSAGES_CLASSES_DECLARATIONS_FMT = '''\
class {database_name}QtMessage_{message_name} : public {database_name}QtMessage
{{
    using {database_name}QtMessage::{database_name}QtMessage;

    void received(const {entity_frame_type} &frame) {{
        {database_name}QtSignals &signals_store = {database_name}QtSignals::instance();

        m_timestamp = {frame_timestamp_function}

        if (!m_valid) {{
            m_valid = true;
            emit on_valid(QDateTime::fromMSecsSinceEpoch(m_timestamp));
        }}

        if (is_extended != {frame_is_extended}) return;
        if (m_length != static_cast<uint>({frame_length_function})) return;

        {database_name}_{message_name}_unpack(
                    &store,
                    {frame_payload_function}{frame_length_parameter}
                    );

{signals_received_code}

    }}

public:
    struct {database_name}_{message_name}_t store;
}};
'''

QT_SOURCE_FMT = '''\
/**
 * This file was generated by:
 * "{commandline}"
 * version {version} {date}.
 */

#include "{database_name}_qt.h"
#include "{database_name}.h"

#include <{entity_frame_type}>
#include <QDebug>

void QVariantHistorySignal{database_name}::update(QDateTime t) {{
    m_data.append(QPair<QDateTime, QVariant>(t, m_val));
}}

void QVariantHistorySignal{database_name}::update_valid(QDateTime t) {{

/*
    if (this->parent->m_valid) {{
        if (m_data.count() > 0)
            m_data.append(QPair<QDateTime, QVariant>(t, QVariant()));
    }} else {{
        m_data.append(QPair<QDateTime, QVariant>(t, QVariant()));
    }}
*/
}}

{database_name}QtSignals::{database_name}QtSignals(QObject *) {{
    {signals_instantiations}
}}

{signals_send_methods}

void {database_name}QtMessages::can_receive_frame_callback(const {entity_frame_type} &frame) {{
    {database_name}QtMessage *msg;
    uint offset = 0;
    {frame_id_offset_calculation}
    msg = {database_name}QtMessages::instance().map.value(offset + {frame_id_function}, nullptr);
    if (msg) msg->received(frame);
}}

void {database_name}QtMessage::send_frame(QByteArray payload, bool is_extended) {{
#if {frame_has_send_frame}
    {entity_frame_type} frame = {entity_frame_type}(m_frameId, payload);

    frame.setExtendedFrameFormat(is_extended);
    frame.setFlexibleDataRateFormat(false);
    // frame.setBitrateSwitch(false);
    frame.setFrameType({entity_frame_type}::DataFrame);

    // qDebug() << "Emit send frame " << frame.toString();

    emit {database_name}QtMessages::instance().sendFrame(frame);
#endif
}}
'''

"""
    return: 
	signals_classes_declarations x signal
	signals_variables
        signals_properties
	messages_classes_declarations
	messages_instantations
        messages_check_validity
"""
def _generate_qt_declarations(database_name, messages, signals, args):

    signals_classes_declarations = list()
    signals_properties = list()
    signals_variables = list()
    messages_classes_declarations = list()
    messages_instantations = list()
    messages_check_validity = list()

    for signal in signals:
        signal.database_name = database_name
        signals_variables.append("QVariantSignal_%(snake_name)s *m_%(snake_name)s;" % signal.__dict__)
        signals_properties.append("Q_PROPERTY(QVariantSignal%(database_name)s* %(snake_name)s MEMBER m_%(snake_name)s CONSTANT)" % signal.__dict__)

    
    for message in messages:
        message.database_name = database_name

        signals_received_code = list()
        for signal in message.used_signals:
            if args.no_floating_point_numbers:
                MY_QT_SIGNALS_RECEIVED_CODE_FMT = QT_SIGNALS_RECEIVED_CODE_WITHOUT_ENCDEC_FMT
            else:
                MY_QT_SIGNALS_RECEIVED_CODE_FMT = QT_SIGNALS_RECEIVED_CODE_FMT
            signals_received_code.append(MY_QT_SIGNALS_RECEIVED_CODE_FMT.format(
                database_name=database_name,
                message_name=message.snake_name,
    	        signal_name=signal.snake_name
    	    ))
            
        if args.for_modbus:
            s = QT_MESSAGES_CLASSES_DECLARATIONS_FMT.format(
                database_name=database_name,
                message_name=message.snake_name,
                message_id=hex(message.frame_id),
                message_is_extended=str(message.is_extended_frame).lower(),
                message_length=message.length,
                signals_received_code='\n'.join(signals_received_code),
                entity_frame_type="QModbusReply",
                frame_length_function="frame.result().valueCount() * 2",
                frame_length_parameter="" if args.no_size_and_memset else ",\n                    static_cast<size_t>(frame.result().valueCount() * 2)",
                frame_payload_function="reinterpret_cast<unsigned char*>(frame.result().values().data())",
                frame_timestamp_function="QDateTime::currentMSecsSinceEpoch();",
                frame_is_extended="true"
                )
        else:
            s = QT_MESSAGES_CLASSES_DECLARATIONS_FMT.format(
                database_name=database_name,
                message_name=message.snake_name,
                message_id=hex(message.frame_id),
                message_is_extended=str(message.is_extended_frame).lower(),
                message_length=message.length,
                signals_received_code='\n'.join(signals_received_code),
                entity_frame_type="QCanBusFrame",
                frame_length_function="frame.payload().length()",
                frame_length_parameter="" if args.no_size_and_memset else ",\n                    static_cast<size_t>(frame.payload().length())",
                frame_payload_function="reinterpret_cast<unsigned char*>(frame.payload().data())",
                frame_timestamp_function="((frame.timeStamp().seconds() * 1000) + (frame.timeStamp().microSeconds() / 1000));",
                frame_is_extended="frame.hasExtendedFrameFormat()"
                )
            
        messages_classes_declarations.append(s)

        messages_instantations.append("        map[{message_id}] = new {database_name}QtMessage_{message_name}({specific_parameters_values} {message_id}, {message_is_extended}, {message_length}, {message_cycle_time});".format(
            database_name=database_name,
            message_name=message.snake_name,
            message_id=hex(message.frame_id),
            message_length=message.length,
            message_is_extended=str(message.is_extended_frame).lower(),
            message_cycle_time=message.cycle_time,
            specific_parameters_values=("%s," % message.node.dbc.attributes.get("StationAddress", 1).value) if args.for_modbus else ""
            ))

        if (message.cycle_time != 0):
            messages_check_validity.append('        map[{message_id}]->check_exipiration_timestamp(now);'.format(
                message_id=hex(message.frame_id),
                ))
        
    for signal in signals:
        signal.database_name = database_name
        # Use class QVariantHistorySignal_xxx when adopting m_map and saving of values
        # Use class QVariantSignal_xxx otherwise (without m_map)
        # 0: NoPersistent 1: StoreWhenChange 2: StoreEveryPeriodSec
        persistent_attribute = signal.dbc.attributes.get("PersistentType", None)
        persistent_attribute = persistent_attribute.value if persistent_attribute else 0
        signal.history_type = "History" if persistent_attribute == 1 else ""

        signals_classes_declarations.append("""
class QVariantSignal_%(snake_name)s : public QVariant%(history_type)sSignal%(database_name)s {
    using QVariant%(history_type)sSignal%(database_name)s::QVariant%(history_type)sSignal%(database_name)s;
    void send(QVariant x);
};
""" % signal.__dict__)
    
    return '\n'.join(signals_classes_declarations), '\n    '.join(signals_properties), '\n    '.join(signals_variables), '\n'.join(messages_classes_declarations), '\n'.join(messages_instantations), '\n'.join(messages_check_validity)


"""
    return: signals_instantiations, signals_send_methods
"""
def _generate_qt_definitions(database_name, signals, args):
    signals_instantiations = list()
    signals_send_methods = list()
    
    for signal in signals:

        if signal.is_float:
            signal._maximum = signal._decimal._maximum
            signal._minimum = signal._decimal._minimum

        elif signal.maximum_value == signal.minimum_value:
            signal._maximum = signal.maximum_type_value
            signal._minimum = signal.minimum_type_value
            
        else:
            signal._maximum = signal.maximum if signal.maximum != None else  signal.maximum_value
            signal._minimum = signal.minimum if signal.minimum != None else  signal.minimum_value
    
        signal._scale = signal._scale or "QVariant()"
        signal._unit = signal._unit or ""

        signals_instantiations.append('m_{signal_name} = new QVariantSignal_{signal_name}({database_name}QtMessages::instance().map[{message_id}], {signal_max}, {signal_min}, {signal_precision}, "{signal_unit}");'.format(
            signal_name=signal.snake_name,
            database_name=database_name,
            message_id=hex(signal.message.frame_id),
            signal_max = signal._maximum,
            signal_min = signal._minimum,
            signal_unit = signal._unit,
            signal_precision = signal._scale
            ))
        print("%s: %s-%s" % (signal.snake_name, signal._minimum, signal._maximum))

        signals_send_methods.append(QT_SIGNALS_SEND_METHODS_FMT.format(
            database_name=database_name,
            signal_name=signal.snake_name,
    	    message_name=signal.message.snake_name,
            message_length_parameter="" if args.no_size_and_memset else f", {signal.message.length}",
            message_length=signal.message.length,
            message_is_extended=str(signal.message.is_extended_frame).lower(),
            variant_cast="toFloat" if signal.as_float or signal.is_float else "toInt" if signal._minimum < 0 else "toUInt",
            type_name=signal.type_name
            ))
    
    return '\n    '.join(signals_instantiations), '\n'.join(signals_send_methods)
    

def generate_qt(database,
             database_name,
             header_name,
             source_name,
             signals,
             args):
    """Generate C source code from given CAN database `database`.

    `database_name` is used as a prefix for all defines, data
    structures and functions.

    `header_name` is the file name of the C header file, which is
    included by the C source file.

    `source_name` is the file name of the C source file, which is
    needed by the fuzzer makefile.

    `signals` are a list of signals to which declare properties and
    emit signals _changed.

    This function returns a tuple of the C header and source files as
    strings.

    """

    date = time.ctime()
    messages = [Message(message) for message in database.messages]

    signals_qt = set()
    messages_qt = set()

    # Attach to message the node property
    for msg in messages:
        msg.node = next(n for n in database.nodes if n.name == next(iter(msg._senders or []), None))
    
    if signals.strip() == "":
        signals = "all"

    if signals == "all":
        def iterate_managed_signals():
            for msg in messages:
                for sig in msg.signals:
                    yield msg, sig
    else:
        def iterate_managed_signals():
            for signal in signals.split(","):
                if signal == '': continue
                for msg in messages:
                    signal_qt = msg.get_signal_by_name(signal)
                    if signal_qt:
                        yield msg, signal_qt
                        break
                else:
                    raise(Exception("unknown signal %s" % signal))

    for msg, signal_qt in iterate_managed_signals():
        if not getattr(msg, "used_signals", False): msg.used_signals = set()
        msg.used_signals.add(signal_qt)
        signal_qt.message = msg
        signals_qt.add(signal_qt)
        messages_qt.add(msg)

    include_guard = '{}_QT_H'.format(database_name.upper())

    # H
    signals_classes_declarations, signals_properties, signals_variables, messages_classes_declarations, messages_instantations, messages_check_validity = _generate_qt_declarations(
			       database_name,
                   messages_qt,
                   signals_qt,
                   args)

    header = QT_HEADER_FMT.format(commandline=" ".join(sys.argv),
                   version=__version__,
                   date=date,
                   include_guard=include_guard,
                   database_name=database_name,
			       signals_classes_declarations=signals_classes_declarations,
			       signals_variables=signals_variables,
			       signals_properties =signals_properties,
			       messages_classes_declarations=messages_classes_declarations,
			       messages_instantations=messages_instantations,
                   messages_check_validity=messages_check_validity,
                   entity_frame_type="QModbusReply" if args.for_modbus else "QCanBusFrame",
                   specific_parameters_definitions="uint stationAddress," if args.for_modbus else "",
                   specific_parameters_declarations="const uint m_stationAddress;" if args.for_modbus else "",
                   specific_parameters_initializations="m_stationAddress(stationAddress)," if args.for_modbus else "",
                   )

    # CPP
    signals_instantiations, signals_send_methods = _generate_qt_definitions(database_name,
                   signals_qt,
                   args)

    offset_calculation_for_modbus="""switch(frame.result().registerType()) {
    case QModbusDataUnit::Invalid: offset = 0; break;
    case QModbusDataUnit::Coils: offset = 1; break;
    case QModbusDataUnit::DiscreteInputs: offset = 10001; break;
    case QModbusDataUnit::InputRegisters: offset = 30001; break;
    case QModbusDataUnit::HoldingRegisters: offset = 40001; break;
    }"""


    source = QT_SOURCE_FMT.format(commandline=" ".join(sys.argv),
                   version=__version__,
                   date=date,
                   header=header_name,
                   database_name=database_name,
                   signals_instantiations=signals_instantiations,
			       signals_send_methods=signals_send_methods,
                   entity_frame_type="QModbusReply" if args.for_modbus else "QCanBusFrame",
                   frame_id_function="static_cast<uint>(frame.result().startAddress())" if args.for_modbus else "frame.frameId()",
                   frame_has_send_frame="0" if args.for_modbus else "1",
                   frame_id_offset_calculation=offset_calculation_for_modbus if args.for_modbus else ""
                   )

    return header, source

