import QtQuick 1.0

Rectangle {
    width: 240; height: 320;

    resources: [
         Component {
            id: contactDelegate
            Text {
                text: modelData.firstName + " " + modelData.lastName
            }
        }
    ]

    ListView {
        anchors.fill: parent
        model: myModel
    }
}
