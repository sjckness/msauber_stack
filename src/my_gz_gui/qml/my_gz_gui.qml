import QtQuick 2.9
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3

// ─── Root: fill the docked panel and enable scrolling ───────────────────────
Rectangle {
  id: root
  anchors.fill: parent
  color: "#1e1e24"

  // ── Scroll view so the panel never clips its content ────────────────────
  ScrollView {
    id: scroller
    anchors.fill: parent
    clip: true
    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
    ScrollBar.vertical.policy: ScrollBar.AsNeeded

    // The actual content column – give it a fixed width so the scroll bar
    // stays out of the way and content doesn't reflux when it appears.
    ColumnLayout {
      width: scroller.width - 12   // 12 px reserved for the vertical scrollbar
      spacing: 8

      // ── Top padding ─────────────────────────────────────────────────────
      Item { height: 6 }

      // ════════════════════════════════════════════════════════════════════
      // SECTION: Robot selection
      // ════════════════════════════════════════════════════════════════════
      SectionLabel { text: "MSAUBER Control" }

      RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        spacing: 8

        FieldLabel { text: "Robot:" }
        ComboBox {
          id: controlEntityCombo
          Layout.fillWidth: true
          model: my_gz_gui.robotList
          currentIndex: model.length > 0 ? 0 : -1
          onCurrentTextChanged: my_gz_gui.OnSelectRobot(currentText)
        }
      }

      Divider {}

      // ════════════════════════════════════════════════════════════════════
      // SECTION: Spawn / Despawn
      // ════════════════════════════════════════════════════════════════════
      SectionLabel { text: "Spawn / Despawn" }

      GridLayout {
        columns: 4
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        columnSpacing: 8; rowSpacing: 4

        FieldLabel { text: "Model:" }
        ComboBox {
          id: spawnModelCombo
          Layout.fillWidth: true
          model: my_gz_gui.spawnableList
          currentIndex: model.length > 0 ? 0 : -1
        }
        Item { Layout.fillWidth: true }
        Item { Layout.fillWidth: true }

        FieldLabel { text: "Name:" }
        TextField {
          id: spawnName
          Layout.fillWidth: true
          placeholderText: spawnModelCombo.currentText
            ? spawnModelCombo.currentText.replace("model://", "").replace(/-/g, "_")
            : "es. cone_orange_1"
        }
        Item { Layout.fillWidth: true }
        Item { Layout.fillWidth: true }

        FieldLabel { text: "X:" }
        TextField { id: spawnX; Layout.fillWidth: true; text: "0.0" }
        FieldLabel { text: "R:" }
        TextField { id: spawnR; Layout.fillWidth: true; text: "0.0" }

        FieldLabel { text: "Y:" }
        TextField { id: spawnY; Layout.fillWidth: true; text: "0.0" }
        FieldLabel { text: "P:" }
        TextField { id: spawnP; Layout.fillWidth: true; text: "0.0" }

        FieldLabel { text: "Z:" }
        TextField { id: spawnZ; Layout.fillWidth: true; text: "0.0" }
        FieldLabel { text: "Yaw:" }
        TextField { id: spawnYaw; Layout.fillWidth: true; text: "0.0" }
      }

      RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        spacing: 8
        Button {
          text: "Spawn"
          Layout.fillWidth: true
          onClicked: my_gz_gui.OnSpawnModel(
            spawnModelCombo.currentText, spawnName.text,
            parseFloat(spawnX.text), parseFloat(spawnY.text),
            parseFloat(spawnZ.text), parseFloat(spawnR.text),
            parseFloat(spawnP.text), parseFloat(spawnYaw.text))
        }
        Button {
          text: "Despawn"
          Layout.fillWidth: true
          onClicked: my_gz_gui.OnRemoveModel(spawnName.text)
        }
      }

      Button {
        text: "Refresh entities"
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        onClicked: my_gz_gui.RefreshModelList()
      }

      Divider {}

      // ════════════════════════════════════════════════════════════════════
      // SECTION: Goal Pose
      // ════════════════════════════════════════════════════════════════════
      SectionLabel { text: "Goal Pose" }

      GridLayout {
        columns: 4
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        columnSpacing: 8; rowSpacing: 4

        FieldLabel { text: "X:" }
        TextField { id: goalX; Layout.fillWidth: true; text: "0.0" }
        FieldLabel { text: "R:" }
        TextField { id: goalR; Layout.fillWidth: true; text: "0.0" }

        FieldLabel { text: "Y:" }
        TextField { id: goalY; Layout.fillWidth: true; text: "0.0" }
        FieldLabel { text: "P:" }
        TextField { id: goalP; Layout.fillWidth: true; text: "0.0" }

        FieldLabel { text: "Z:" }
        TextField { id: goalZ; Layout.fillWidth: true; text: "0.0" }
        FieldLabel { text: "Yaw:" }
        TextField { id: goalYaw; Layout.fillWidth: true; text: "0.0" }
      }

      Button {
        text: "Send Goal"
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        onClicked: my_gz_gui.OnSendGoalPose(
          parseFloat(goalX.text), parseFloat(goalY.text),
          parseFloat(goalZ.text), parseFloat(goalR.text),
          parseFloat(goalP.text), parseFloat(goalYaw.text))
      }

      Divider {}

      // ════════════════════════════════════════════════════════════════════
      // SECTION: Physics
      // ════════════════════════════════════════════════════════════════════
      SectionLabel { text: "Physics" }

      RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        spacing: 8
        FieldLabel { text: "Gravity Z:" }
        TextField { id: gravityZ; Layout.fillWidth: true; text: "-9.81" }
        Button {
          text: "Apply"
          onClicked: my_gz_gui.OnSetGravity(parseFloat(gravityZ.text))
        }
      }

      Divider {}

      // ════════════════════════════════════════════════════════════════════
      // SECTION: Camera / YOLO viewer
      // ════════════════════════════════════════════════════════════════════
      RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8

        SectionLabel {
          text: "Camera"
          Layout.fillWidth: true
        }

        // Camera on/off toggle
        Button {
          id: cameraToggleBtn
          checkable: true
          checked: true
          implicitWidth: 68
          implicitHeight: 26
          padding: 0

          background: Rectangle {
            radius: height / 2
            color: cameraToggleBtn.checked ? "#2e7d32" : "#555"
            Rectangle {
              width: parent.height - 4
              height: width; radius: width / 2
              y: 2
              x: cameraToggleBtn.checked ? parent.width - width - 2 : 2
              color: "white"
              Behavior on x { NumberAnimation { duration: 120 } }
            }
          }
          contentItem: Item {}
        }
      }

      // ── Tab bar: Raw | YOLO ────────────────────────────────────────────
      TabBar {
        id: imageTabBar
        visible: cameraToggleBtn.checked
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8

        TabButton {
          text: "Raw"
          width: implicitWidth
        }
        TabButton {
          text: "YOLO"
          width: implicitWidth
          // Dim when no YOLO data yet
          opacity: my_gz_gui.yoloAvailable ? 1.0 : 0.45
        }
      }

      // ── Image display ──────────────────────────────────────────────────
      Rectangle {
        id: imageBox
        visible: cameraToggleBtn.checked
        Layout.fillWidth: true
        Layout.leftMargin: 8; Layout.rightMargin: 8
        height: 220
        color: "#12151c"
        radius: 6
        border.color: imageTabBar.currentIndex === 1 && my_gz_gui.yoloAvailable
                      ? "#f59e0b" : "#3a3f4b"
        border.width: 1
        clip: true

        // ── Raw camera image ─────────────────────────────────────────────
        Image {
          anchors.fill: parent; anchors.margins: 1
          fillMode: Image.PreserveAspectFit
          cache: false
          visible: imageTabBar.currentIndex === 0
          source: my_gz_gui.cameraImageSource

          Label {
            anchors.centerIn: parent
            visible: my_gz_gui.cameraImageSource === ""
            text: "Waiting for /front_camera/image …"
            color: "#8a9bb0"
            font.pixelSize: 11
          }
        }

        // ── YOLO-annotated image ─────────────────────────────────────────
        Image {
          anchors.fill: parent; anchors.margins: 1
          fillMode: Image.PreserveAspectFit
          cache: false
          visible: imageTabBar.currentIndex === 1
          source: my_gz_gui.yoloImageSource

          Label {
            anchors.centerIn: parent
            visible: !my_gz_gui.yoloAvailable
            text: "YOLO not running\nLaunch with  use_yolo:=true"
            horizontalAlignment: Text.AlignHCenter
            color: "#8a9bb0"
            font.pixelSize: 11
          }
        }

        // ── YOLO badge (top-right corner) ────────────────────────────────
        Rectangle {
          anchors.top: parent.top; anchors.right: parent.right
          anchors.margins: 6
          visible: imageTabBar.currentIndex === 1 && my_gz_gui.yoloAvailable
          width: yoloBadgeLabel.implicitWidth + 10
          height: 18; radius: 4
          color: "#f59e0b"
          Label {
            id: yoloBadgeLabel
            anchors.centerIn: parent
            text: "YOLO ●"
            color: "#1e1e24"
            font.pixelSize: 10; font.bold: true
          }
        }
      }

      // ── Bottom padding ───────────────────────────────────────────────
      Item { height: 10 }
    }  // end ColumnLayout
  }  // end ScrollView

  // ── Inline component helpers (QML 2.15+; works in Qt 5.15 / Gazebo Harmonic) ─
  component SectionLabel : Label {
    Layout.fillWidth: true
    Layout.leftMargin: 8; Layout.topMargin: 4
    font.pixelSize: 13; font.bold: true
    color: "#e2e8f0"
  }

  component FieldLabel : Label {
    color: "#a0aec0"
    font.pixelSize: 12
  }

  component Divider : Rectangle {
    Layout.fillWidth: true
    Layout.leftMargin: 8; Layout.rightMargin: 8
    height: 1; color: "#2d3748"
  }
}
