// src/pages/Register.tsx
import { useState } from 'react';
import { Form, Input, Button, Typography, Card, message, Space, Select, Divider } from 'antd';
import { MailOutlined, LockOutlined, UserOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { POSSIBLE_INTEREST_KEYWORDS } from '../config';
import '../components/css/AuthPages.css';

/*
    Register page component that provides a form for users to create a new account.
    
    The page includes:  
    - A title and subtitle inviting users to sign up.  
    - A form with fields for first name, last name, email, password, confirm password, and interests.
    - Interest keywords are mandatory, interest text is optional.
    - A submit button that triggers the registration process.  
    - A link for users who already have an account to navigate to the login page.

    The component uses Ant Design components for styling and layout,
    and it interacts with the authentication context to perform the registration operation.
*/

const { Title, Text } = Typography;

interface RegisterFormValues {
    email: string;
    password: string;
    confirmPassword: string;
    first_name: string;
    last_name: string;
    interest_keys: string[];
    interest_text?: string;
}

export default function Register() {

    // State to manage loading state during registration process
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const [messageApi, contextHolder] = message.useMessage();

    const onFinish = async (values: RegisterFormValues) => {

        setLoading(true);
        try {
            await register({
                email: values.email,
                password: values.password,
                first_name: values.first_name,
                last_name: values.last_name,
                interest_keys: values.interest_keys,
                interest_text: values.interest_text || '',
            });

            messageApi.success('Registration successful! Generating your event recommendations...');
            navigate('/events');
        } catch (error) {
            messageApi.error(error instanceof Error ? error.message : 'Registration failed');
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
                        <Title level={2} className="auth-title">Create Account</Title>
                        <Text type="secondary">Sign up for a new account</Text>
                    </div>

                    <Form
                        name="register"
                        onFinish={onFinish}
                        layout="vertical"
                        size="large"
                    >
                        <Form.Item
                            name="first_name"
                            rules={[
                                { required: true, message: 'Please enter your first name' },
                            ]}
                        >
                            <Input
                                prefix={<UserOutlined />}
                                placeholder="First Name"
                            />
                        </Form.Item>

                        <Form.Item
                            name="last_name"
                            rules={[
                                { required: true, message: 'Please enter your last name' },
                            ]}
                        >
                            <Input
                                prefix={<UserOutlined />}
                                placeholder="Last Name"
                            />
                        </Form.Item>

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

                        <Form.Item
                            name="password" //Name of form
                            rules={[
                                { required: true, message: 'Please enter your password' },
                                { min: 6, message: 'Password must be at least 6 characters' },
                            ]}
                        >
                            <Input.Password
                                prefix={<LockOutlined />}
                                placeholder="Password"
                            />
                        </Form.Item>

                        <Form.Item
                            name="confirmPassword"
                            dependencies={['password']}
                            rules={[
                                { required: true, message: 'Please confirm your password' },

                                /*
                                    Validator to check if passwords match

                                    getFieldValue is provided by Ant Design to get 
                                    the value of other fields

                                    validator() is provided by Ant Design to define
                                    custom validation logic
                                */
                                ({ getFieldValue }) => ({

                                    // Syntax: validator(_rule, value)

                                    validator(_, value) {

                                        //getFieldValue() takes the name of the field as argument
                                        if (!value || getFieldValue('password') === value) {

                                            //Promise.resolve() indicates validation success
                                            return Promise.resolve();
                                        }

                                        return Promise.reject(new Error('Passwords do not match'));
                                    },
                                }),
                            ]}
                        >
                            <Input.Password
                                prefix={<LockOutlined />}
                                placeholder="Confirm Password"
                            />
                        </Form.Item>

                        <Divider>Your Interests</Divider>
                        
                        <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                            Select your interests to receive personalized event recommendations. You can change these later in Settings.
                        </Text>

                        <Form.Item
                            name="interest_keys"
                            label="Interest Keywords"
                            rules={[
                                { required: true, message: 'Please select at least one interest' },
                                { type: 'array', min: 1, message: 'Please select at least one interest' },
                            ]}
                        >
                            <Select
                                mode="multiple"
                                placeholder="Select your interests"
                                options={POSSIBLE_INTEREST_KEYWORDS.map(keyword => ({ 
                                    label: keyword, 
                                    value: keyword 
                                }))}
                                allowClear
                            />
                        </Form.Item>

                        <Form.Item
                            name="interest_text"
                            label="Additional Interests (Optional)"
                        >
                            <Input.TextArea 
                                rows={3} 
                                placeholder="Describe any additional interests not covered above..." 
                            />
                        </Form.Item>

                        <Form.Item>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={loading}
                                block
                            >
                                Sign Up
                            </Button>
                        </Form.Item>
                    </Form>

                    <div className="auth-text-center">
                        <Text type="secondary">
                            Already have an account?{' '}
                            <Link to="/login">Sign in</Link>
                        </Text>
                    </div>
                </Space>
            </Card>
        </div>
    );
}
