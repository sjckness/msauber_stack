import QtQuick 2.9
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3

Rectangle {
  id: root
  anchors.fill: parent
  color: "#f5f5f5"
  Layout.minimumWidth: 600
  Layout.minimumHeight: 600
  property bool cameraViewEnabled: true

  Timer {
    id: initTimer
    interval: 1000
    running: true
    repeat: false
    onTriggered: my_gz_gui.RefreshModelList()
  }

  Timer {
    id: autoRefreshTimer
    interval: 60000
    running: true
    repeat: true
    onTriggered: my_gz_gui.RefreshModelList()
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: 10
    spacing: 8

    Label {
      text: "MSAUBER Control"
      font.pixelSize: 14
      font.bold: true
    }

    RowLayout {
      Layout.fillWidth: true
      spacing: 8

      Label { text: "Robot:" }
      ComboBox {
        id: controlEntityCombo
        Layout.fillWidth: true
        model: my_gz_gui.robotList
        currentIndex: model.length > 0 ? 0 : -1
        onCurrentTextChanged: my_gz_gui.OnSelectRobot(currentText)
      }
    }

    Rectangle { Layout.fillWidth: true; height: 1; color: "#ccc" }

    Label {
      text: "Spawn / Despawn"
      font.pixelSize: 14
      font.bold: true
    }

    GridLayout {
      columns: 4
      Layout.fillWidth: true
      columnSpacing: 8
      rowSpacing: 4

      Label { text: "Model:" }
      ComboBox {
        id: spawnModelCombo
        Layout.fillWidth: true
        model: my_gz_gui.spawnableList
        currentIndex: model.length > 0 ? 0 : -1
      }
      Item { Layout.fillWidth: true }
      Item { Layout.fillWidth: true }

      Label { text: "Name:" }
      TextField {
        id: spawnName
        Layout.fillWidth: true
        placeholderText: spawnModelCombo.currentText
          ? spawnModelCombo.currentText.replace("model://", "").replace(/-/g, "_")
          : "es. cone_orange_1"
      }
      Item { Layout.fillWidth: true }
      Item { Layout.fillWidth: true }

      Label { text: "X:" }
      TextField { id: spawnX; Layout.fillWidth: true; text: "0.0" }
      Label { text: "R:" }
      TextField { id: spawnR; Layout.fillWidth: true; text: "0.0" }

      Label { text: "Y:" }
      TextField { id: spawnY; Layout.fillWidth: true; text: "0.0" }
      Label { text: "P:" }
      TextField { id: spawnP; Layout.fillWidth: true; text: "0.0" }

      Label { text: "Z:" }
      TextField { id: spawnZ; Layout.fillWidth: true; text: "0.0" }
      Label { text: "Y:" }
      TextField { id: spawnYaw; Layout.fillWidth: true; text: "0.0" }
    }

    RowLayout {
      Layout.fillWidth: true
      Button {
        text: "Spawn"
        Layout.fillWidth: true
        onClicked: my_gz_gui.OnSpawnModel(
          spawnModelCombo.currentText, spawnName.text,
          parseFloat(spawnX.text),
          parseFloat(spawnY.text),
          parseFloat(spawnZ.text),
          parseFloat(spawnR.text),
          parseFloat(spawnP.text),
          parseFloat(spawnYaw.text))
      }
      Button {
        text: "Despawn"
        Layout.fillWidth: true
        onClicked: my_gz_gui.OnRemoveModel(spawnName.text)
      }
    }

    Button {
      text: "update entities"
      Layout.fillWidth: true
      onClicked: my_gz_gui.RefreshModelList()
    }

    Rectangle { Layout.fillWidth: true; height: 1; color: "#ccc" }

    Label {
      text: "Goal Pose"
      font.pixelSize: 14
      font.bold: true
    }

    GridLayout {
      columns: 4
      Layout.fillWidth: true
      columnSpacing: 8
      rowSpacing: 4

      Label { text: "X:" }
      TextField { id: goalX; Layout.fillWidth: true; text: "0.0" }
      Label { text: "R:" }
      TextField { id: goalR; Layout.fillWidth: true; text: "0.0" }

      Label { text: "Y:" }
      TextField { id: goalY; Layout.fillWidth: true; text: "0.0" }
      Label { text: "P:" }
      TextField { id: goalP; Layout.fillWidth: true; text: "0.0" }

      Label { text: "Z:" }
      TextField { id: goalZ; Layout.fillWidth: true; text: "0.0" }
      Label { text: "Y:" }
      TextField { id: goalYaw; Layout.fillWidth: true; text: "0.0" }
    }

    Button {
      text: "Send Goal"
      Layout.fillWidth: true
      onClicked: my_gz_gui.OnSendGoalPose(
        parseFloat(goalX.text),
        parseFloat(goalY.text),
        parseFloat(goalZ.text),
        parseFloat(goalR.text),
        parseFloat(goalP.text),
        parseFloat(goalYaw.text))
    }

    Rectangle { Layout.fillWidth: true; height: 1; color: "#ccc" }

    Label {
      text: "Physics"
      font.pixelSize: 14
      font.bold: true
    }

    RowLayout {
      Layout.fillWidth: true
      spacing: 8

      Label { text: "Gravity Z:" }
      TextField {
        id: gravityZ
        Layout.fillWidth: true
        text: "-9.81"
      }
      Button {
        text: "Apply"
        onClicked: my_gz_gui.OnSetGravity(parseFloat(gravityZ.text))
      }
    }

    RowLayout {
      Layout.fillWidth: true
      spacing: 8

      Label {
        Layout.fillWidth: true
        text: controlEntityCombo.currentText + " front camera"
        font.pixelSize: 14
        font.bold: true
      }

      Button {
        id: cameraToggleBtn
        checkable: true
        checked: root.cameraViewEnabled
        implicitWidth: 76
        implicitHeight: 48
        onToggled: root.cameraViewEnabled = checked
        padding: 0

        background: Rectangle {
          radius: height / 2
          color: cameraToggleBtn.checked ? "#2e7d32" : "#9aa5b1"
          border.width: 1
          border.color: cameraToggleBtn.checked ? "#1b5e20" : "#6b7280"

          Rectangle {
            width: parent.height - 6
            height: width
            radius: width / 2
            y: 3
            x: cameraToggleBtn.checked ? parent.width - width - 3 : 3
            color: "white"
          }
        }

        contentItem: Item {
          Text {
            anchors.left: parent.left
            anchors.leftMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            text: "cam"
            color: "white"
            font.pixelSize: 13
            font.bold: true
          }
        }
      }
    }

    Rectangle {
      Layout.fillWidth: true
      Layout.preferredHeight: root.cameraViewEnabled ? 220 : 0
      visible: root.cameraViewEnabled
      color: "#20242c"
      radius: 6
      border.color: "#4a5568"
      border.width: 1
      clip: true

      Image {
        anchors.fill: parent
        anchors.margins: 1
        fillMode: Image.PreserveAspectFit
        cache: false
        source: my_gz_gui.cameraImageSource
      }

      Label {
        anchors.centerIn: parent
        visible: my_gz_gui.cameraImageSource === ""
        text: controlEntityCombo.currentText === "" ?
          "Select a robot" :
          "waiting for  " + controlEntityCombo.currentText +" camera"
        color: "#e2e8f0"
      }
    }

    Item { Layout.fillHeight: true }
  }
}
