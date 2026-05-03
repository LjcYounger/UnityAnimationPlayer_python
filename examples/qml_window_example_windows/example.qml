import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Particles 2.15

Item {
    id: container
    
    property real originalWidth: 120
    property real originalHeight: 40
    property var animatedButtons: ({})
    property var ballInitPos: Qt.point(0, 0)
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        
        Rectangle {
            id: ballContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"
            border.color: "black"
            border.width: 1
            
            onWidthChanged: {
                ball.y = height - ball.height - 10
                ballInitPos = Qt.point(ball.x + ball.width / 2, ball.y + ball.height / 2)
            }

            ParticleSystem {
                id: ballTrail
                anchors.fill: parent
                running: true

                ImageParticle {
                    source: "circle.png"
                    color: "blue"
                    entryEffect: ImageParticle.None
                }

                Emitter {
                    id: trailEmitter
                    system: ballTrail
                    // 绑定到球的中心位置
                    x: ball.x + ball.width / 2
                    y: ball.y + ball.height / 2
                    lifeSpan: 20000
                    size: 8
                    emitRate: 100
                    velocity: PointDirection { x: 0; y: 0 }
                    acceleration: PointDirection { x: 0; y: 0 }
                }
            }

            Rectangle {
                id: ball
                width: 30
                height: 30
                radius: 15
                color: "red"
                x: 10
                y: 10

                transform: [
                    Scale {
                        id: ballScale
                        origin.x: ball.width / 2
                        origin.y: ball.height / 2
                    },
                    Rotation {
                        id: ballRotation
                        origin.x: ball.width / 2
                        origin.y: ball.height / 2
                    }
                ]
            }
        }
        
        RowLayout {
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            height: 60

            Button {
                id: showChildWindowButton
                text: "Child Window(No Button Animation)"
                Layout.preferredWidth: container.originalWidth
                Layout.preferredHeight: container.originalHeight
                
                transform: [
                    Scale {
                        origin.x: width / 2
                        origin.y: height / 2
                    },
                    Rotation {
                        origin.x: width / 2
                        origin.y: height / 2
                    }
                ]
                
                onPressed: exampleWindow.show_child_window()
            }

            Item { Layout.fillWidth: true }
            
            Text {
                text: "Playing Speed: " + valueSlider.value.toFixed(2)
                Layout.preferredHeight: container.originalHeight
                verticalAlignment: Text.AlignVCenter
            }

            Slider {
                id: valueSlider
                objectName: "valueSlider"
                from: -5
                to: 5
                value: 1
                stepSize: 0.01
                Layout.preferredWidth: 100
                Layout.preferredHeight: container.originalHeight
                onValueChanged: exampleWindow.on_slider_value_changed(value)
            }

            Button {
                id: playBallAnimationButton
                objectName: "playBallAnimationButton"
                text: "Play Ball Animation"
                Layout.preferredWidth: container.originalWidth
                Layout.preferredHeight: container.originalHeight
                
                transform: [
                    Scale {
                        origin.x: container.originalWidth / 2
                        origin.y: container.originalHeight / 2
                    },
                    Rotation {
                        origin.x: container.originalWidth / 2
                        origin.y: container.originalHeight / 2
                    }
                ]
                
                onPressed: {
                    exampleWindow.on_button_pressed(objectName)
                    exampleWindow.on_ball_animation_button_pressed()
                }
                onReleased: exampleWindow.on_button_released(objectName)
                Component.onCompleted: animatedButtons[objectName] = this
            }

            Button {
                id: replayWindowAnimationButton
                objectName: "replayWindowAnimationButton"
                text: "Reshow Window"
                Layout.preferredWidth: container.originalWidth
                Layout.preferredHeight: container.originalHeight
                
                transform: [
                    Scale {
                        origin.x: container.originalWidth / 2
                        origin.y: container.originalHeight / 2
                    },
                    Rotation {
                        origin.x: container.originalWidth / 2
                        origin.y: container.originalHeight / 2
                    }
                ]
                
                onPressed: {
                    exampleWindow.on_button_pressed(objectName)
                    exampleWindow.replay_window_animation()
                }
                onReleased: exampleWindow.on_button_released(objectName)
                Component.onCompleted: animatedButtons[objectName] = this
            }
        }
    }
    function updateButtonTransform(buttonName,  
                        rotationAngle = undefined, 
                        scaleX = undefined, 
                        scaleY = undefined) {
        if (animatedButtons[buttonName]) {
            var button = animatedButtons[buttonName]
            
            if (scaleX !== undefined) {button.transform[0].xScale = scaleX}
            if (scaleY !== undefined) {button.transform[0].yScale = scaleY}
            
            if (rotationAngle !== undefined) {button.transform[1].angle = rotationAngle}
        }
    }

    function updateBallTransform(centerX, centerY, scaleX, scaleY, rotationAngle) {
        if (scaleX !== undefined) ball.transform[0].xScale = scaleX
        if (scaleY !== undefined) ball.transform[0].yScale = scaleY
        if (rotationAngle !== undefined) ball.transform[1].angle = rotationAngle
        
        if (centerX !== undefined) ball.x = ballInitPos.x + centerX - ball.width / 2
        if (centerY !== undefined) ball.y = ballInitPos.y - centerY - ball.height / 2
    }

    function resetBallTransform() {
        ball.x = ballInitPos.x - ball.width / 2
        ball.y = ballInitPos.y - ball.height / 2
        ball.transform[0].xScale = 1
        ball.transform[0].yScale = 1
        ball.transform[1].angle = 0
    }

    function enableBallTrail() { ballTrail.running = true }
    function disableBallTrail() { ballTrail.running = false }
}