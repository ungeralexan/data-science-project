// src/pages/ForgotPassword.tsx
import { useState } from 'react';
import { Form, Input, Button, Typography, Card, message, Space, Alert } from 'antd';
import { MailOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import '../components/css/AuthPages.css';
import { API_BASE_URL } from '../config';

const { Title, Text } = Typography;

interface ForgotPasswordFormValues {
    email: string;
}

export default function ForgotPassword() {
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();

    //Makes POST request to backend to initiate password reset process
    const onFinish = async (values: ForgotPasswordFormValues) => {

        setLoading(true);
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
                method: 'POST', // POST = create data
                headers: {
                    'Content-Type': 'application/json',
                },
                
                body: JSON.stringify({ email: values.email }),
            });

            const data = await response.json();

            if (response.ok) {
                setSubmitted(true);
            } else {
                messageApi.error(data.detail || 'Something went wrong');
            }
        } catch {
            messageApi.error('Failed to send reset request');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            {contextHolder}
            <Card className="auth-card">
                <Space direction="vertical" size="large" className="auth-space-full-width">
                    <div className="auth-text-center">
                        <Title level={2} className="auth-title">Forgot Password</Title>
                        <Text type="secondary">
                            Enter your email address and we'll send you a link to reset your password.
                        </Text>
                    </div>

                    {/* submitted is Ant Design state */}
                    {submitted ? (
                        <Space direction="vertical" size="middle" className="auth-space-full-width">
                            <Alert
                                message="Check your email"
                                description="If an account with that email exists, we've sent a password reset link. Please check your inbox (and spam folder)."
                                type="success"
                                showIcon
                            />

                            <div className="auth-text-center">
                                <Link to="/login">
                                    <Button type="link">Back to Login</Button>
                                </Link>
                            </div>
                        </Space>

                    //Alternative to submitted state
                    ) : (
                        <>
                            <Form
                                name="forgot-password"
                                onFinish={onFinish}
                                layout="vertical"
                                size="large"
                            >
                                <Form.Item
                                    name="email"
                                    rules={[
                                        { required: true, message: 'Please enter your email' },
                                        { type: 'email', message: 'Please enter a valid email' },
                                    ]}
                                >
                                    <Input
                                        prefix={<MailOutlined />}
                                        placeholder="Email"
                                    />
                                </Form.Item>

                                <Form.Item>
                                    <Button
                                        type="primary"
                                        htmlType="submit"
                                        loading={loading}
                                        block
                                    >
                                        Send Reset Link
                                    </Button>
                                </Form.Item>
                            </Form>

                            <div className="auth-text-center">
                                <Text type="secondary">
                                    Remember your password?{' '}
                                    <Link to="/login">Sign in</Link>
                                </Text>
                            </div>
                        </>
                    )}
                </Space>
            </Card>
        </div>
    );
}
