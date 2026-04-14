#ifndef MY_GZ_GUI__MYGUIPLUGIN_HH_
#define MY_GZ_GUI__MYGUIPLUGIN_HH_

#include <memory>

#include <QStringList>

#include <gz/gui/Plugin.hh>

namespace my_gz_gui
{

class MyGuiPlugin : public gz::gui::Plugin
{
  Q_OBJECT

  Q_PROPERTY(QString pluginTitle      READ PluginTitle        CONSTANT)
  Q_PROPERTY(QStringList modelList    READ ModelList          NOTIFY modelListChanged)
  Q_PROPERTY(QStringList robotList    READ RobotList          NOTIFY robotListChanged)
  Q_PROPERTY(QStringList spawnableList READ SpawnableList     NOTIFY spawnableListChanged)

  /// Raw camera feed (Gazebo transport image, topic: /front_camera/image)
  Q_PROPERTY(QString cameraImageSource READ CameraImageSource NOTIFY cameraImageSourceChanged)

  /// YOLO-annotated image (ROS topic: /perception/annotated_image)
  Q_PROPERTY(QString yoloImageSource  READ YoloImageSource    NOTIFY yoloImageSourceChanged)

  /// True once at least one YOLO-annotated frame has been received
  Q_PROPERTY(bool yoloAvailable       READ YoloAvailable      NOTIFY yoloAvailableChanged)

public:
  MyGuiPlugin();
  ~MyGuiPlugin() override;

  void LoadConfig(const tinyxml2::XMLElement *_pluginElem) override;

  QString    PluginTitle()       const;
  QStringList ModelList()        const;
  QStringList RobotList()        const;
  QStringList SpawnableList()    const;
  QString    CameraImageSource() const;
  QString    YoloImageSource()   const;
  bool       YoloAvailable()     const;

signals:
  void modelListChanged();
  void robotListChanged();
  void spawnableListChanged();
  void cameraImageSourceChanged();
  void yoloImageSourceChanged();
  void yoloAvailableChanged();

public slots:
  void OnSetPose(const QString &modelName,
                 double x, double y, double z, double yaw);

  void OnSpawnModel(const QString &modelUri,
                    const QString &modelName,
                    double x, double y, double z,
                    double roll, double pitch, double yaw);

  void OnRemoveModel(const QString &modelName);

  void OnSetGravity(double gz);
  void OnSendGoalPose(double x, double y, double z,
                      double roll, double pitch, double yaw);

  void RefreshModelList();
  void OnSelectRobot(const QString &robotName);

private:
  struct Impl;
  std::unique_ptr<Impl> impl;
};

}  // namespace my_gz_gui

#endif  // MY_GZ_GUI__MYGUIPLUGIN_HH_
